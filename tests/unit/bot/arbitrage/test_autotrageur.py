import getpass
from collections import namedtuple
from unittest.mock import Mock

import ccxt
import pytest
import schedule
import yaml

import bot.arbitrage.autotrageur
import fp_libs.db.maria_db_handler as db_handler
from bot.arbitrage.autotrageur import (Autotrageur,
                                       AutotrageurAuthenticationError)
from bot.common.config_constants import DB_NAME, DB_USER
from bot.trader.dry_run import DryRunExchange, DryRunManager
from fp_libs.constants.ccxt_constants import API_KEY, API_SECRET, PASSWORD
from fp_libs.utils.ccxt_utils import RetryableError

OpenAndSafeLoad = namedtuple('OpenAndSafeLoad', ['open', 'safe_load'])


class Mocktrageur(Autotrageur):
    """Mock concrete class. ABC's cannot be instantiated."""

    def _alert(self, subject, exception):
        pass

    def _poll_opportunity(self):
        pass

    def _execute_trade(self):
        pass

    def _clean_up(self):
        pass

    def _export_state(self):
        pass

    def _import_state(self, previous_state):
        pass


@pytest.fixture(scope='module')
def autotrageur():
    result = Mocktrageur()
    result._config = Mock()
    return result


@pytest.fixture()
def mock_open_yaml(mocker):
    fake_open = mocker.patch('builtins.open', mocker.mock_open())
    fake_yaml = mocker.patch.object(yaml, 'safe_load')
    return OpenAndSafeLoad(fake_open, fake_yaml)


def test_parse_config_file(mocker, autotrageur, mock_open_yaml):
    file_name = 'fakefile'

    parsed_config = autotrageur._Autotrageur__parse_config_file(file_name)
    assert(parsed_config != {})
    mock_open_yaml.open.assert_called_once_with(file_name, 'r')
    mock_open_yaml.safe_load.assert_called_once()


@pytest.mark.parametrize(
    "decrypt_success, dryrun", [
        (True, True),
        (True, False),
        (False, True),
        pytest.param(False, False,
            marks=pytest.mark.xfail(strict=True, raises=IOError)),
    ]
)
def test_parse_keyfile(mocker, autotrageur, decrypt_success, dryrun):
    args = mocker.MagicMock()
    mocker.patch('getpass.getpass')
    mocker.patch.object(autotrageur._config, 'dryrun', dryrun)
    mock_decrypt = mocker.patch.object(bot.arbitrage.autotrageur, 'decrypt')
    mock_kf_to_map = mocker.patch.object(bot.arbitrage.autotrageur, 'keyfile_to_map')

    if not decrypt_success:
        mock_decrypt.side_effect = Exception

    key_map = autotrageur._Autotrageur__parse_keyfile(args)

    getpass.getpass.assert_called_once_with(prompt="Enter keyfile password:")   # pylint: disable=E1101
    if decrypt_success:
        mock_decrypt.assert_called_once()
        mock_kf_to_map.assert_called_once()
        assert(key_map)
    elif not dryrun:
        mock_decrypt.assert_called_once()
        mock_kf_to_map.assert_not_called()
        assert key_map is None
    else:
        mock_decrypt.assert_called_once()
        mock_kf_to_map.assert_not_called()
        assert not (key_map)


def test_load_configs(mocker, autotrageur):
    MOCK_CONFIG_PATH = 'mock/config/path'
    mock_parse_config_file = mocker.patch.object(
        autotrageur, '_Autotrageur__parse_config_file')
    mock_configuration = mocker.patch('bot.arbitrage.autotrageur.Configuration')
    mock_uuid4 = mocker.patch('uuid.uuid4')
    mock_time_time = mocker.patch('time.time')

    autotrageur._load_configs(MOCK_CONFIG_PATH)

    autotrageur._Autotrageur__parse_config_file.assert_called_once_with(
        MOCK_CONFIG_PATH)
    mock_configuration.assert_called_once_with(
        id=str(mock_uuid4.return_value),
        start_timestamp=int(mock_time_time.return_value),
        **mock_parse_config_file)
    assert autotrageur._config is not None


def test_init_db(mocker, autotrageur, mock_open_yaml):
    MOCK_DB_NAME = 'SUM_DB_NAME'
    MOCK_DB_PASSWORD = 'FAKE_DB_PASSWORD'
    MOCK_DB_USER = 'SUM_DUM_GUY'
    MOCK_DB_CONFIG_PATH = 'fake/db/config/path'
    mocker.patch('getpass.getpass', return_value=MOCK_DB_PASSWORD)
    mocker.patch.object(db_handler, 'start_db')
    mocker.spy(schedule, 'every')
    mock_open_yaml.safe_load.return_value = {
        DB_USER: MOCK_DB_USER,
        DB_NAME: MOCK_DB_NAME
    }

    autotrageur._Autotrageur__init_db(MOCK_DB_CONFIG_PATH)

    getpass.getpass.assert_called_once_with(prompt="Enter database password:")  # pylint: disable=E1101
    mock_open_yaml.open.assert_called_once_with(MOCK_DB_CONFIG_PATH, 'r')
    mock_open_yaml.safe_load.assert_called_once()
    db_handler.start_db.assert_called_once_with(        # pylint: disable=E1101
        MOCK_DB_USER,
        MOCK_DB_PASSWORD,
        MOCK_DB_NAME)
    schedule.every.assert_called_once_with(7)           # pylint: disable=E1101
    assert len(schedule.jobs) == 1
    schedule.clear()



@pytest.mark.parametrize('env_path_exists', [True, False])
@pytest.mark.parametrize('env_path_loaded', [True, False])
@pytest.mark.parametrize('env_var_loaded', [True, False])
def test_load_env_vars(mocker, autotrageur, env_path_exists, env_path_loaded,
                       env_var_loaded):
    mock_env_file = mocker.Mock()
    mocker.patch.object(bot.arbitrage.autotrageur, 'Path', return_value=mock_env_file)
    mocker.patch.object(mock_env_file, 'exists', return_value=env_path_exists)
    mocker.patch.object(bot.arbitrage.autotrageur, 'load_dotenv', return_value=env_path_loaded)
    mocker.patch('bot.arbitrage.autotrageur.ENV_VAR_NAMES', ['FAKE_ENV_VAR_NAME'])
    mocker.patch('os.getenv', return_value=env_var_loaded)

    result = autotrageur._Autotrageur__load_env_vars()
    assert result is (env_path_exists and env_path_loaded and env_var_loaded)


@pytest.mark.parametrize("resume_id", [None, 'abcdef'])
@pytest.mark.parametrize("dryrun", [True, False])
def test_setup_dry_run(mocker, autotrageur, resume_id, dryrun):
    dry_run_exchange_init = mocker.patch.object(
        DryRunExchange, '__init__', return_value=None)
    dry_run_manager_init = mocker.patch.object(
        DryRunManager, '__init__', return_value=None)
    mocker.patch.object(autotrageur._config, 'dryrun', dryrun)
    mocker.patch.object(autotrageur._config, 'exchange1_pair', 'ETH/USD')
    mocker.patch.object(autotrageur._config, 'exchange2_pair', 'ETH/KRW')

    autotrageur._Autotrageur__setup_dry_run(resume_id)

    if resume_id and dryrun:
        assert dry_run_exchange_init.call_count == 0
        assert dry_run_manager_init.call_count == 0
    elif dryrun:
        assert dry_run_exchange_init.call_count == 2
        assert dry_run_manager_init.call_count == 1
        assert isinstance(autotrageur._dry_run_manager, DryRunManager)
    else:
        assert autotrageur._dry_run_manager is None

@pytest.mark.parametrize('exc_type', [ccxt.AuthenticationError, ccxt.ExchangeNotAvailable])
@pytest.mark.parametrize('balance_check_success', [True, False])
@pytest.mark.parametrize('use_test_api', [True, False])
@pytest.mark.parametrize('dryrun', [True, False])
def test_setup_traders(mocker, autotrageur, dryrun, use_test_api,
                       balance_check_success, exc_type):
    fake_slippage = 0.25
    fake_pair = 'fake/pair'
    fake_exchange_key_map = {
        'fake': {
            API_KEY: 'API_KEY',
            API_SECRET: 'API_SECRET',
            PASSWORD: 'PASSWORD'
        },
        'pair': {
            API_KEY: 'API_KEY',
            API_SECRET: 'API_SECRET',
            PASSWORD: 'PASSWORD'
        }
    }
    placeholder = 'fake'
    mock_trader1 = mocker.Mock()
    mock_trader2 = mocker.Mock()
    mock_ccxt_trader_constructor = mocker.patch('bot.arbitrage.autotrageur.CCXTTrader')
    mock_ccxt_trader_constructor.side_effect = [mock_trader1, mock_trader2]
    mocker.patch.object(autotrageur._config, 'exchange1_pair', fake_pair)
    mocker.patch.object(autotrageur._config, 'exchange2_pair', fake_pair)
    mocker.patch.object(autotrageur._config, 'exchange1', placeholder)
    mocker.patch.object(autotrageur._config, 'exchange2', placeholder)
    mocker.patch.object(autotrageur._config, 'slippage', fake_slippage)
    mocker.patch.object(autotrageur._config, 'use_test_api', use_test_api)
    mocker.patch.object(autotrageur._config, 'dryrun', dryrun)
    if dryrun:
        mocker.patch.object(
            autotrageur,
            '_dry_run_manager',
            DryRunManager(mocker.Mock(), mocker.Mock()),
            create=True)

    # If wallet balance fetch fails, expect either ccxt.AuthenticationError or
    # ccxt.ExchangeNotAvailable to be raised.
    if balance_check_success is False:
        # For testing purposes, only need one trader to throw an exception.
        mock_trader1.update_wallet_balances.side_effect = exc_type
        with pytest.raises(AutotrageurAuthenticationError):
            autotrageur._Autotrageur__setup_traders(fake_exchange_key_map)

        # Expect called once and encountered exception.
        mock_trader1.update_wallet_balances.assert_called_once_with()
        mock_trader2.update_wallet_balances.assert_not_called()
    else:
        autotrageur._Autotrageur__setup_traders(fake_exchange_key_map)
        mock_trader1.update_wallet_balances.assert_called_once_with()
        mock_trader2.update_wallet_balances.assert_called_once_with()
        assert(mock_trader1.load_markets.call_count == 1)
        assert(mock_trader2.load_markets.call_count == 1)

    if use_test_api:
        assert(mock_trader1.connect_test_api.call_count == 1)
        assert(mock_trader2.connect_test_api.call_count == 1)
    else:
        assert(mock_trader1.connect_test_api.call_count == 0)
        assert(mock_trader2.connect_test_api.call_count == 0)


def test_post_setup(mocker, autotrageur):
    args = mocker.MagicMock()
    MOCK_EXCHANGE_KEY_MAP = mocker.Mock()
    mock_parse_keyfile = mocker.patch.object(
        autotrageur, '_Autotrageur__parse_keyfile', return_value=MOCK_EXCHANGE_KEY_MAP)
    mock_setup_dry_run = mocker.patch.object(autotrageur, '_Autotrageur__setup_dry_run')
    mock_setup_traders = mocker.patch.object(autotrageur, '_Autotrageur__setup_traders')

    autotrageur._post_setup(args)
    mock_parse_keyfile.assert_called_once_with(args['KEYFILE'], args['--pi_mode'])
    mock_setup_dry_run.assert_called_once_with(args['--resume_id'])
    mock_setup_traders.assert_called_once_with(MOCK_EXCHANGE_KEY_MAP)


@pytest.mark.parametrize('env_vars_loaded', [True, False])
def test_setup(mocker, autotrageur, env_vars_loaded):
    args = mocker.MagicMock()
    mock_load_env_vars = mocker.patch.object(
        autotrageur, '_Autotrageur__load_env_vars', return_value=env_vars_loaded)
    mock_init_db = mocker.patch.object(autotrageur, '_Autotrageur__init_db')

    if env_vars_loaded:
        autotrageur._setup(args)
        mock_load_env_vars.assert_called_once_with()
        mock_init_db.assert_called_once_with(args['DBCONFIGFILE'])
    else:
        with pytest.raises(EnvironmentError):
            autotrageur._setup(args)
        mock_load_env_vars.assert_called_once_with()
        mock_init_db.assert_not_called()


def test_wait(mocker, autotrageur):
    MOCK_DEFAULT_WAIT = 5
    mocker.patch.object(autotrageur._config, 'poll_wait_default', MOCK_DEFAULT_WAIT)
    mock_time_sleep = mocker.patch('time.sleep')
    autotrageur._wait()
    mock_time_sleep.assert_called_once_with(MOCK_DEFAULT_WAIT)

class TestRunAutotrageur:
    FAKE_RESUME_ID = '12345'
    FAKE_ARGS_NEW_RUN = {
        'FAKE': 'ARGS',
        'CONFIGFILE': 'path/to/config/file',
        '--resume_id': None
    }
    FAKE_ARGS_RESUME_RUN = {
        'FAKE': 'ARGS',
        'CONFIGFILE': 'path/to/config/file',
        '--resume_id': FAKE_RESUME_ID
    }

    def _setup_mocks(self, mocker, autotrageur):
        # Use SystemExit to stop the infinite loop.
        mocker.patch.object(autotrageur, '_alert')
        mocker.patch.object(autotrageur, '_setup')
        mocker.patch.object(autotrageur, '_post_setup')
        mocker.patch.object(autotrageur, '_clean_up', create=True)
        mocker.patch.object(autotrageur, '_execute_trade')
        mocker.patch.object(autotrageur, '_export_state')
        mocker.patch.object(autotrageur, '_wait', side_effect=[
            None, None, None, None, SystemExit
        ])
        mocker.patch.object(autotrageur, '_load_configs')

    @pytest.mark.parametrize("resume_or_new_args", [
        FAKE_ARGS_NEW_RUN,
        FAKE_ARGS_RESUME_RUN])
    @pytest.mark.parametrize("requires_configs", [True, False])
    def test_run_autotrageur(self, mocker, autotrageur, requires_configs, resume_or_new_args):
        self._setup_mocks(mocker, autotrageur)
        mocker.patch.object(autotrageur, '_poll_opportunity', side_effect=[
            True, True, False, True, False
        ])
        mock_counter = mocker.patch('bot.arbitrage.autotrageur.RetryCounter')
        retry_counter_instance = mock_counter.return_value

        with pytest.raises(SystemExit):
            autotrageur.run_autotrageur(resume_or_new_args, requires_configs)

        autotrageur._alert.assert_not_called()
        autotrageur._setup.assert_called_once_with(resume_or_new_args)
        autotrageur._post_setup.assert_called_once_with(resume_or_new_args)
        autotrageur._export_state.assert_not_called()
        assert autotrageur._clean_up.call_count == 5
        assert autotrageur._wait.call_count == 5
        assert autotrageur._poll_opportunity.call_count == 5
        assert autotrageur._execute_trade.call_count == 3
        assert retry_counter_instance.increment.call_count == 5

        if requires_configs and not resume_or_new_args['--resume_id']:
            autotrageur._load_configs.assert_called_once_with(resume_or_new_args['CONFIGFILE'])

    @pytest.mark.parametrize("dryrun", [True, False])
    def test_run_autotrageur_keyboard_interrupt(self, mocker, autotrageur,
                                                dryrun):
        self._setup_mocks(mocker, autotrageur)
        mocker.patch.object(autotrageur, '_poll_opportunity', side_effect=[
            True, True, False, KeyboardInterrupt, False
        ])
        mocker.patch.object(autotrageur._config, 'dryrun', dryrun)
        mock_counter = mocker.patch('bot.arbitrage.autotrageur.RetryCounter')
        retry_counter_instance = mock_counter.return_value

        if dryrun:
            mocker.patch.object(autotrageur, '_dry_run_manager', create=True)
            mocker.patch.object(autotrageur._dry_run_manager, 'log_all', create=True)
            autotrageur.run_autotrageur(self.FAKE_ARGS_NEW_RUN)
        else:
            with pytest.raises(KeyboardInterrupt):
                autotrageur.run_autotrageur(self.FAKE_ARGS_NEW_RUN)

        autotrageur._alert.assert_not_called()
        autotrageur._setup.assert_called_once_with(self.FAKE_ARGS_NEW_RUN)
        autotrageur._post_setup.assert_called_once_with(self.FAKE_ARGS_NEW_RUN)
        autotrageur._load_configs.assert_called_with(self.FAKE_ARGS_NEW_RUN['CONFIGFILE'])
        autotrageur._export_state.assert_called_once_with()
        assert autotrageur._clean_up.call_count == 4
        assert autotrageur._wait.call_count == 3
        assert autotrageur._poll_opportunity.call_count == 4
        assert autotrageur._execute_trade.call_count == 2
        assert retry_counter_instance.increment.call_count == 3

        if dryrun:
            autotrageur._dry_run_manager.log_all.assert_called_once_with()

    @pytest.mark.parametrize("exc_type", [
        AutotrageurAuthenticationError,
        ccxt.ExchangeError,
        Exception
    ])
    @pytest.mark.parametrize("dryrun", [True, False])
    def test_run_autotrageur_exception(self, mocker, autotrageur, exc_type,
                                       dryrun):
        self._setup_mocks(mocker, autotrageur)
        mocker.patch.object(autotrageur, '_poll_opportunity', side_effect=[
            True, exc_type, False, True, False
        ])
        mocker.patch.object(autotrageur._config, 'dryrun', dryrun)

        if dryrun:
            mocker.patch.object(autotrageur, '_dry_run_manager', create=True)
            with pytest.raises(exc_type):
                autotrageur.run_autotrageur(self.FAKE_ARGS_NEW_RUN)
            autotrageur._alert.assert_called_once()
        else:
            # Save original function before mocking out `run_autotrageur`
            autotrageur.original_run_autotrageur = autotrageur.run_autotrageur

            mocker.spy(autotrageur, 'original_run_autotrageur')
            mocker.patch.object(autotrageur, 'run_autotrageur')
            mocker.patch.object(autotrageur, '_dry_run_manager', None, create=True)
            autotrageur.original_run_autotrageur(self.FAKE_ARGS_NEW_RUN)

            autotrageur._alert.assert_called_once()
            assert autotrageur._config.dryrun is True

            # Perhaps redundant checks, but ensures that the two are differentiated.
            autotrageur.original_run_autotrageur.assert_called_once_with(
                self.FAKE_ARGS_NEW_RUN)
            autotrageur.run_autotrageur.assert_called_once_with(
                self.FAKE_ARGS_NEW_RUN, False)

        autotrageur._setup.assert_called_once_with(self.FAKE_ARGS_NEW_RUN)
        autotrageur._post_setup.assert_called_once_with(self.FAKE_ARGS_NEW_RUN)
        autotrageur._load_configs.assert_called_with(self.FAKE_ARGS_NEW_RUN['CONFIGFILE'])
        autotrageur._export_state.assert_called_once_with()
        assert autotrageur._clean_up.call_count == 2
        assert autotrageur._wait.call_count == 1
        assert autotrageur._poll_opportunity.call_count == 2
        assert autotrageur._execute_trade.call_count == 1

    @pytest.mark.parametrize("decrement_returns", [
        [True, True, False], [True, True, True]])
    def test_run_autotrageur_retry_exception(self, mocker, autotrageur,
                                             decrement_returns):
        self._setup_mocks(mocker, autotrageur)
        mocker.patch.object(autotrageur, '_poll_opportunity', side_effect=[
            True, RetryableError, RetryableError, RetryableError, SystemExit
        ])
        mocker.patch.object(autotrageur._config, 'dryrun', True)
        mock_counter = mocker.patch('bot.arbitrage.autotrageur.RetryCounter')
        retry_counter_instance = mock_counter.return_value
        retry_counter_instance.decrement.side_effect = decrement_returns

        if decrement_returns[2]:
            # With a third successful retry, the SystemExit side effect
            # on the 5th _poll_opportunity will be triggered.
            with pytest.raises(SystemExit):
                autotrageur.run_autotrageur(self.FAKE_ARGS_NEW_RUN)

            assert autotrageur._poll_opportunity.call_count == 5
            assert autotrageur._clean_up.call_count == 5
            assert autotrageur._wait.call_count == 4
        else:
            with pytest.raises(RetryableError):
                autotrageur.run_autotrageur(self.FAKE_ARGS_NEW_RUN)

            assert autotrageur._poll_opportunity.call_count == 4
            assert autotrageur._clean_up.call_count == 4
            assert autotrageur._wait.call_count == 3

        autotrageur._setup.assert_called_once_with(self.FAKE_ARGS_NEW_RUN)
        autotrageur._post_setup.assert_called_once_with(self.FAKE_ARGS_NEW_RUN)
        autotrageur._load_configs.assert_called_with(self.FAKE_ARGS_NEW_RUN['CONFIGFILE'])
        assert autotrageur._execute_trade.call_count == 1
        assert retry_counter_instance.increment.call_count == 1
