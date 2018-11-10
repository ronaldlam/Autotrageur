import getpass
from collections import namedtuple
from unittest.mock import Mock

import ccxt
import pytest
import schedule
import yaml

import autotrageur.bot.arbitrage.autotrageur
import fp_libs.db.maria_db_handler as db_handler
from autotrageur.bot.arbitrage.autotrageur import (Autotrageur,
                                                   AutotrageurAuthenticationError)
from autotrageur.bot.common.config_constants import DB_NAME, DB_USER
from autotrageur.bot.trader.dry_run import DryRunExchange
from fp_libs.constants.ccxt_constants import API_KEY, API_SECRET, PASSWORD
from fp_libs.utilities import num_to_decimal
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
def mock_autotrageur():
    result = Mocktrageur()
    result._config = Mock()
    return result


@pytest.fixture()
def mock_open_yaml(mocker):
    fake_open = mocker.patch('builtins.open', mocker.mock_open())
    fake_yaml = mocker.patch.object(yaml, 'safe_load')
    return OpenAndSafeLoad(fake_open, fake_yaml)


def test_parse_config_file(mocker, mock_autotrageur, mock_open_yaml):
    file_name = 'fakefile'

    parsed_config = mock_autotrageur._Autotrageur__parse_config_file(file_name)
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
def test_parse_keyfile(mocker, mock_autotrageur, decrypt_success, dryrun):
    args = mocker.MagicMock()
    mocker.patch('getpass.getpass')
    mocker.patch.object(mock_autotrageur._config, 'dryrun', dryrun)
    mock_decrypt = mocker.patch.object(autotrageur.bot.arbitrage.autotrageur, 'decrypt')
    mock_kf_to_map = mocker.patch.object(autotrageur.bot.arbitrage.autotrageur, 'keyfile_to_map')

    if not decrypt_success:
        mock_decrypt.side_effect = Exception

    key_map = mock_autotrageur._Autotrageur__parse_keyfile(args)

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


def test_load_configs(mocker, mock_autotrageur):
    MOCK_CONFIG_PATH = 'mock/config/path'
    mock_parse_config_file = mocker.patch.object(
        mock_autotrageur, '_Autotrageur__parse_config_file')
    mock_configuration = mocker.patch('autotrageur.bot.arbitrage.autotrageur.Configuration')
    mock_uuid4 = mocker.patch('uuid.uuid4')
    mock_time_time = mocker.patch('time.time')

    mock_autotrageur._load_configs(MOCK_CONFIG_PATH)

    mock_autotrageur._Autotrageur__parse_config_file.assert_called_once_with(
        MOCK_CONFIG_PATH)
    mock_configuration.assert_called_once_with(
        id=str(mock_uuid4.return_value),
        start_timestamp=int(mock_time_time.return_value),
        **mock_parse_config_file)
    assert mock_autotrageur._config is not None


def test_init_db(mocker, mock_autotrageur, mock_open_yaml):
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

    mock_autotrageur._Autotrageur__init_db(MOCK_DB_CONFIG_PATH)

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


def test_init_temp_logger(mocker, mock_autotrageur):
    mock_setup_temp_logger = mocker.patch.object(
        autotrageur.bot.arbitrage.autotrageur.bot_logging,
        'setup_temporary_logger')

    mock_autotrageur._Autotrageur__init_temp_logger()

    assert mock_autotrageur.logger == mock_setup_temp_logger.return_value


@pytest.mark.parametrize('dryrun, use_test_api, result_log_dir', [
    (True, True, 'dryrun-test'),
    (True, False, 'dryrun'),
    (False, True, 'test'),
    (False, False, 'live'),
])
def test_init_complete_logger(mocker, mock_autotrageur, dryrun, use_test_api,
                     result_log_dir):
    mock_logger = mocker.Mock()
    mocker.patch.object(mock_autotrageur, 'logger', mock_logger, create=True)
    mocker.patch.object(mock_autotrageur._config, 'dryrun', dryrun)
    mocker.patch.object(mock_autotrageur._config, 'use_test_api', use_test_api)
    mock_setup_background_logger = mocker.patch.object(
        autotrageur.bot.arbitrage.autotrageur.bot_logging,
        'setup_background_logger')

    mock_autotrageur._Autotrageur__init_complete_logger()

    mock_setup_background_logger.assert_called_once_with(
        mock_logger, result_log_dir, mock_autotrageur._config.id)
    mock_setup_background_logger.return_value.queue_listener.start.assert_called_once()


@pytest.mark.parametrize('env_path_exists', [True, False])
@pytest.mark.parametrize('env_path_loaded', [True, False])
@pytest.mark.parametrize('env_var_loaded', [True, False])
def test_load_env_vars(mocker, mock_autotrageur, env_path_exists, env_path_loaded,
                       env_var_loaded):
    mock_env_file = mocker.Mock()
    mocker.patch.object(autotrageur.bot.arbitrage.autotrageur, 'Path', return_value=mock_env_file)
    mocker.patch.object(mock_env_file, 'exists', return_value=env_path_exists)
    mocker.patch.object(autotrageur.bot.arbitrage.autotrageur, 'load_dotenv', return_value=env_path_loaded)
    mocker.patch('autotrageur.bot.arbitrage.autotrageur.ENV_VAR_NAMES', ['FAKE_ENV_VAR_NAME'])
    mocker.patch('os.getenv', return_value=env_var_loaded)

    result = mock_autotrageur._Autotrageur__load_env_vars()
    assert result is (env_path_exists and env_path_loaded and env_var_loaded)


def test_setup_dry_run_exchanges(mocker, mock_autotrageur):
    MOCK_E1 = 'Gemini'
    MOCK_E2 = 'Bithumb'
    MOCK_E1_PAIR = 'ETH/USD'
    MOCK_E2_PAIR = 'ETH/KRW'
    MOCK_E1_BASE_BAL = 5
    MOCK_E1_QUOTE_BAL = 2000
    MOCK_E2_BASE_BAL = 10
    MOCK_E2_QUOTE_BAL = 20000

    mocker.patch.object(mock_autotrageur._config, 'exchange1', MOCK_E1)
    mocker.patch.object(mock_autotrageur._config, 'exchange2', MOCK_E2)
    mocker.patch.object(mock_autotrageur._config, 'exchange1_pair', MOCK_E1_PAIR)
    mocker.patch.object(mock_autotrageur._config, 'exchange2_pair', MOCK_E2_PAIR)
    mocker.patch.object(mock_autotrageur._config, 'dryrun_e1_base', MOCK_E1_BASE_BAL)
    mocker.patch.object(mock_autotrageur._config, 'dryrun_e1_quote', MOCK_E1_QUOTE_BAL)
    mocker.patch.object(mock_autotrageur._config, 'dryrun_e2_base', MOCK_E2_BASE_BAL)
    mocker.patch.object(mock_autotrageur._config, 'dryrun_e2_quote', MOCK_E2_QUOTE_BAL)

    mock_dry_e1, mock_dry_e2 = mock_autotrageur._Autotrageur__setup_dry_run_exchanges()

    assert mock_dry_e1.name == MOCK_E1
    assert mock_dry_e1.base == 'ETH'
    assert mock_dry_e1.quote == 'USD'
    assert mock_dry_e1.base_balance == num_to_decimal(MOCK_E1_BASE_BAL)
    assert mock_dry_e1.quote_balance == num_to_decimal(MOCK_E1_QUOTE_BAL)
    assert mock_dry_e2.name == MOCK_E2
    assert mock_dry_e2.base == 'ETH'
    assert mock_dry_e2.quote == 'KRW'
    assert mock_dry_e2.base_balance == num_to_decimal(MOCK_E2_BASE_BAL)
    assert mock_dry_e2.quote_balance == num_to_decimal(MOCK_E2_QUOTE_BAL)

@pytest.mark.parametrize('exc_type', [ccxt.AuthenticationError, ccxt.ExchangeNotAvailable])
@pytest.mark.parametrize('balance_check_success', [True, False])
@pytest.mark.parametrize('use_test_api', [True, False])
@pytest.mark.parametrize('dryrun', [True, False])
def test_setup_traders(mocker, mock_autotrageur, dryrun, use_test_api,
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
    mock_ccxt_trader_constructor = mocker.patch('autotrageur.bot.arbitrage.autotrageur.CCXTTrader')
    mock_ccxt_trader_constructor.side_effect = [mock_trader1, mock_trader2]
    mocker.patch.object(mock_autotrageur._config, 'exchange1_pair', fake_pair)
    mocker.patch.object(mock_autotrageur._config, 'exchange2_pair', fake_pair)
    mocker.patch.object(mock_autotrageur._config, 'exchange1', placeholder)
    mocker.patch.object(mock_autotrageur._config, 'exchange2', placeholder)
    mocker.patch.object(mock_autotrageur._config, 'slippage', fake_slippage)
    mocker.patch.object(mock_autotrageur._config, 'use_test_api', use_test_api)
    mocker.patch.object(mock_autotrageur._config, 'dryrun', dryrun)
    mock_setup_dr_exchanges = mocker.patch.object(
        mock_autotrageur, '_Autotrageur__setup_dry_run_exchanges')
    if dryrun:
        mock_setup_dr_exchanges.return_value = mocker.Mock(), mocker.Mock()

    # If wallet balance fetch fails, expect either ccxt.AuthenticationError or
    # ccxt.ExchangeNotAvailable to be raised.
    if balance_check_success is False:
        # For testing purposes, only need one trader to throw an exception.
        mock_trader1.update_wallet_balances.side_effect = exc_type
        with pytest.raises(AutotrageurAuthenticationError):
            mock_autotrageur._Autotrageur__setup_traders(fake_exchange_key_map)

        # Expect called once and encountered exception.
        mock_trader1.update_wallet_balances.assert_called_once_with()
        mock_trader2.update_wallet_balances.assert_not_called()
    else:
        mock_autotrageur._Autotrageur__setup_traders(fake_exchange_key_map)
        mock_trader1.update_wallet_balances.assert_called_once_with()
        mock_trader2.update_wallet_balances.assert_called_once_with()
        assert(mock_trader1.load_markets.call_count == 1)
        assert(mock_trader2.load_markets.call_count == 1)

    if dryrun:
        assert mock_setup_dr_exchanges.call_count == 1
    else:
        assert mock_setup_dr_exchanges.call_count == 0

    if use_test_api:
        assert(mock_trader1.connect_test_api.call_count == 1)
        assert(mock_trader2.connect_test_api.call_count == 1)
    else:
        assert(mock_trader1.connect_test_api.call_count == 0)
        assert(mock_trader2.connect_test_api.call_count == 0)


def test_post_setup(mocker, mock_autotrageur):
    args = mocker.MagicMock()
    MOCK_EXCHANGE_KEY_MAP = mocker.Mock()
    mock_parse_keyfile = mocker.patch.object(
        mock_autotrageur, '_Autotrageur__parse_keyfile', return_value=MOCK_EXCHANGE_KEY_MAP)
    mock_setup_traders = mocker.patch.object(
        mock_autotrageur, '_Autotrageur__setup_traders')
    mock_init_logger = mocker.patch.object(
        mock_autotrageur, '_Autotrageur__init_complete_logger')

    mock_autotrageur._post_setup(args)
    mock_parse_keyfile.assert_called_once_with(args['KEYFILE'], args['--pi_mode'])
    mock_setup_traders.assert_called_once_with(MOCK_EXCHANGE_KEY_MAP)


@pytest.mark.parametrize('env_vars_loaded', [True, False])
def test_setup(mocker, mock_autotrageur, env_vars_loaded):
    args = mocker.MagicMock()
    mock_init_logger = mocker.patch.object(mock_autotrageur, '_Autotrageur__init_temp_logger')
    mock_load_env_vars = mocker.patch.object(
        mock_autotrageur, '_Autotrageur__load_env_vars', return_value=env_vars_loaded)
    mock_init_db = mocker.patch.object(mock_autotrageur, '_Autotrageur__init_db')

    if env_vars_loaded:
        mock_autotrageur._setup(args)
        mock_load_env_vars.assert_called_once_with()
        mock_init_db.assert_called_once_with(args['DBCONFIGFILE'])
    else:
        with pytest.raises(EnvironmentError):
            mock_autotrageur._setup(args)
        mock_load_env_vars.assert_called_once_with()
        mock_init_db.assert_not_called()

    mock_init_logger.assert_called_once()


def test_wait(mocker, mock_autotrageur):
    MOCK_DEFAULT_WAIT = 5
    mocker.patch.object(mock_autotrageur._config, 'poll_wait_default', MOCK_DEFAULT_WAIT)
    mock_time_sleep = mocker.patch('time.sleep')
    mock_autotrageur._wait()
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

    def _setup_mocks(self, mocker, mock_autotrageur):
        # Use SystemExit to stop the infinite loop.
        mocker.patch.object(mock_autotrageur, '_alert')
        mocker.patch.object(mock_autotrageur, '_setup')
        mocker.patch.object(mock_autotrageur, '_post_setup')
        mocker.patch.object(mock_autotrageur, '_clean_up', create=True)
        mocker.patch.object(mock_autotrageur, '_execute_trade')
        mocker.patch.object(mock_autotrageur, '_export_state')
        mocker.patch.object(mock_autotrageur, '_wait', side_effect=[
            None, None, None, None, SystemExit
        ])
        mocker.patch.object(mock_autotrageur, '_load_configs')

    @pytest.mark.parametrize("resume_or_new_args", [
        FAKE_ARGS_NEW_RUN,
        FAKE_ARGS_RESUME_RUN])
    @pytest.mark.parametrize("requires_configs", [True, False])
    def test_run_autotrageur(self, mocker, mock_autotrageur, requires_configs, resume_or_new_args):
        self._setup_mocks(mocker, mock_autotrageur)
        mocker.patch.object(mock_autotrageur, '_poll_opportunity', side_effect=[
            True, True, False, True, False
        ])
        mock_counter = mocker.patch('autotrageur.bot.arbitrage.autotrageur.RetryCounter')
        retry_counter_instance = mock_counter.return_value

        with pytest.raises(SystemExit):
            mock_autotrageur.run_autotrageur(resume_or_new_args, requires_configs)

        mock_autotrageur._alert.assert_not_called()
        mock_autotrageur._setup.assert_called_once_with(resume_or_new_args)
        mock_autotrageur._post_setup.assert_called_once_with(resume_or_new_args)
        mock_autotrageur._export_state.assert_not_called()
        assert mock_autotrageur._clean_up.call_count == 5
        assert mock_autotrageur._wait.call_count == 5
        assert mock_autotrageur._poll_opportunity.call_count == 5
        assert mock_autotrageur._execute_trade.call_count == 3
        assert retry_counter_instance.increment.call_count == 5

        if requires_configs and not resume_or_new_args['--resume_id']:
            mock_autotrageur._load_configs.assert_called_once_with(resume_or_new_args['CONFIGFILE'])

    @pytest.mark.parametrize("dryrun", [True, False])
    def test_run_autotrageur_keyboard_interrupt(self, mocker, mock_autotrageur,
                                                dryrun):
        self._setup_mocks(mocker, mock_autotrageur)
        mocker.patch.object(mock_autotrageur, '_poll_opportunity', side_effect=[
            True, True, False, KeyboardInterrupt, False
        ])
        mocker.patch.object(mock_autotrageur._config, 'dryrun', dryrun)
        mock_counter = mocker.patch('autotrageur.bot.arbitrage.autotrageur.RetryCounter')
        retry_counter_instance = mock_counter.return_value

        if dryrun:
            mocker.patch.object(mock_autotrageur, '_stat_tracker', create=True)
            mocker.patch.object(mock_autotrageur._stat_tracker, 'log_all', create=True)
            mock_autotrageur.run_autotrageur(self.FAKE_ARGS_NEW_RUN)
        else:
            with pytest.raises(KeyboardInterrupt):
                mock_autotrageur.run_autotrageur(self.FAKE_ARGS_NEW_RUN)

        mock_autotrageur._alert.assert_not_called()
        mock_autotrageur._setup.assert_called_once_with(self.FAKE_ARGS_NEW_RUN)
        mock_autotrageur._post_setup.assert_called_once_with(self.FAKE_ARGS_NEW_RUN)
        mock_autotrageur._load_configs.assert_called_with(self.FAKE_ARGS_NEW_RUN['CONFIGFILE'])
        mock_autotrageur._export_state.assert_called_once_with()
        assert mock_autotrageur._clean_up.call_count == 4
        assert mock_autotrageur._wait.call_count == 3
        assert mock_autotrageur._poll_opportunity.call_count == 4
        assert mock_autotrageur._execute_trade.call_count == 2
        assert retry_counter_instance.increment.call_count == 3

        if dryrun:
            mock_autotrageur._stat_tracker.log_all.assert_called_once_with()

    @pytest.mark.parametrize("exc_type", [
        AutotrageurAuthenticationError,
        ccxt.ExchangeError,
        Exception
    ])
    @pytest.mark.parametrize("dryrun", [True, False])
    def test_run_autotrageur_exception(self, mocker, mock_autotrageur, exc_type,
                                       dryrun):
        self._setup_mocks(mocker, mock_autotrageur)
        mocker.patch.object(mock_autotrageur, '_poll_opportunity', side_effect=[
            True, exc_type, False, True, False
        ])
        mocker.patch.object(mock_autotrageur._config, 'dryrun', dryrun)

        if dryrun:
            with pytest.raises(exc_type):
                mock_autotrageur.run_autotrageur(self.FAKE_ARGS_NEW_RUN)
            mock_autotrageur._alert.assert_called_once()
        else:
            # Save original function before mocking out `run_autotrageur`
            mock_autotrageur.original_run_autotrageur = mock_autotrageur.run_autotrageur

            mocker.spy(mock_autotrageur, 'original_run_autotrageur')
            mocker.patch.object(mock_autotrageur, 'run_autotrageur')

            mock_autotrageur.original_run_autotrageur(self.FAKE_ARGS_NEW_RUN)

            mock_autotrageur._alert.assert_called_once()
            assert mock_autotrageur._config.dryrun is True

            # Perhaps redundant checks, but ensures that the two are differentiated.
            mock_autotrageur.original_run_autotrageur.assert_called_once_with(
                self.FAKE_ARGS_NEW_RUN)
            mock_autotrageur.run_autotrageur.assert_called_once_with(
                self.FAKE_ARGS_NEW_RUN, False)

        mock_autotrageur._setup.assert_called_once_with(self.FAKE_ARGS_NEW_RUN)
        mock_autotrageur._post_setup.assert_called_once_with(self.FAKE_ARGS_NEW_RUN)
        mock_autotrageur._load_configs.assert_called_with(self.FAKE_ARGS_NEW_RUN['CONFIGFILE'])
        mock_autotrageur._export_state.assert_called_once_with()
        assert mock_autotrageur._clean_up.call_count == 2
        assert mock_autotrageur._wait.call_count == 1
        assert mock_autotrageur._poll_opportunity.call_count == 2
        assert mock_autotrageur._execute_trade.call_count == 1

    @pytest.mark.parametrize("decrement_returns", [
        [True, True, False], [True, True, True]])
    def test_run_autotrageur_retry_exception(self, mocker, mock_autotrageur,
                                             decrement_returns):
        self._setup_mocks(mocker, mock_autotrageur)
        mocker.patch.object(mock_autotrageur, '_poll_opportunity', side_effect=[
            True, RetryableError, RetryableError, RetryableError, SystemExit
        ])
        mocker.patch.object(mock_autotrageur._config, 'dryrun', True)
        mock_counter = mocker.patch('autotrageur.bot.arbitrage.autotrageur.RetryCounter')
        retry_counter_instance = mock_counter.return_value
        retry_counter_instance.decrement.side_effect = decrement_returns

        if decrement_returns[2]:
            # With a third successful retry, the SystemExit side effect
            # on the 5th _poll_opportunity will be triggered.
            with pytest.raises(SystemExit):
                mock_autotrageur.run_autotrageur(self.FAKE_ARGS_NEW_RUN)

            assert mock_autotrageur._poll_opportunity.call_count == 5
            assert mock_autotrageur._clean_up.call_count == 5
            assert mock_autotrageur._wait.call_count == 4
        else:
            with pytest.raises(RetryableError):
                mock_autotrageur.run_autotrageur(self.FAKE_ARGS_NEW_RUN)

            assert mock_autotrageur._poll_opportunity.call_count == 4
            assert mock_autotrageur._clean_up.call_count == 4
            assert mock_autotrageur._wait.call_count == 3

        mock_autotrageur._setup.assert_called_once_with(self.FAKE_ARGS_NEW_RUN)
        mock_autotrageur._post_setup.assert_called_once_with(self.FAKE_ARGS_NEW_RUN)
        mock_autotrageur._load_configs.assert_called_with(self.FAKE_ARGS_NEW_RUN['CONFIGFILE'])
        assert mock_autotrageur._execute_trade.call_count == 1
        assert retry_counter_instance.increment.call_count == 1
