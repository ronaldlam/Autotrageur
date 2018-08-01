import getpass
import os
from pathlib import Path

import ccxt
import pytest
import schedule
import yaml

import bot.arbitrage.autotrageur
import libs.db.maria_db_handler as db_handler
import libs.twilio.twilio_client as twilio_client
from bot.arbitrage.autotrageur import Autotrageur
from bot.arbitrage.fcf_autotrageur import AuthenticationError
from bot.common.config_constants import (DB_NAME, DB_USER, DRYRUN,
                                         DRYRUN_E1_BASE, DRYRUN_E1_QUOTE,
                                         DRYRUN_E2_BASE, DRYRUN_E2_QUOTE,
                                         EXCHANGE1, EXCHANGE1_PAIR,
                                         EXCHANGE1_TEST, EXCHANGE2,
                                         EXCHANGE2_PAIR, EXCHANGE2_TEST,
                                         SLIPPAGE, TWILIO_CFG_PATH)
from bot.trader.dry_run import DryRun, DryRunExchange
from libs.security.encryption import decrypt
from libs.utilities import keyfile_to_map
from libs.utils.ccxt_utils import RetryableError


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


@pytest.fixture(scope='module')
def autotrageur():
    result = Mocktrageur()
    result.config = {}
    return result


def test_load_config_file(mocker, autotrageur):
    file_name = 'fakefile'
    fake_open = mocker.patch('builtins.open', mocker.mock_open())
    fake_yaml = mocker.patch.object(yaml, 'safe_load')
    autotrageur._Autotrageur__load_config_file(file_name)
    assert(autotrageur.config != {})
    fake_open.assert_called_once_with(file_name, 'r')
    fake_yaml.assert_called_once()
    autotrageur.config = {}


@pytest.mark.parametrize(
    "succeed, dryrun", [
        (True, True),
        (True, False),
        (False, True),
        pytest.param(False, False,
            marks=pytest.mark.xfail(strict=True, raises=IOError)),
    ]
)
def test_load_keyfile(mocker, autotrageur, succeed, dryrun):
    args = mocker.MagicMock()
    mocker.patch('getpass.getpass')
    mocker.patch.dict(autotrageur.config, { DRYRUN: dryrun })

    if succeed:
        mocker.patch.object(bot.arbitrage.autotrageur, 'decrypt')
        mocker.patch.object(bot.arbitrage.autotrageur, 'keyfile_to_map')

    key_map = autotrageur._Autotrageur__load_keyfile(args)

    getpass.getpass.assert_called_once_with(prompt="Enter keyfile password:")   # pylint: disable=E1101
    if succeed:
        assert(key_map)
    else:
        assert not (key_map)


@pytest.mark.parametrize(
    "keyfile_loaded", [
        True,
        False
    ]
)
def test_load_configs(mocker, autotrageur, keyfile_loaded):
    args = mocker.MagicMock()
    # These are name mangled.
    mocker.patch.object(autotrageur, '_Autotrageur__load_config_file')
    mocker.patch.object(autotrageur, '_Autotrageur__load_db')
    mocker.patch.object(autotrageur, '_Autotrageur__load_env_vars')
    mocker.patch.object(autotrageur, '_Autotrageur__load_keyfile')
    mocker.patch.object(autotrageur, '_Autotrageur__load_twilio')
    mocker.patch.dict(autotrageur.config, {
        EXCHANGE1: 'e1',
        EXCHANGE2: 'e2',
        TWILIO_CFG_PATH: 'some/fake/path'
    })
    if not keyfile_loaded:
        autotrageur._Autotrageur__load_keyfile.return_value = None

    autotrageur._load_configs(args)

    autotrageur._Autotrageur__load_config_file.assert_called_once_with(
        args['CONFIGFILE'])
    autotrageur._Autotrageur__load_db.assert_called_once_with()
    autotrageur._Autotrageur__load_keyfile.assert_called_once_with(args)
    autotrageur._Autotrageur__load_env_vars.assert_called_once_with()
    autotrageur._Autotrageur__load_twilio.assert_called_once_with(
        autotrageur.config[TWILIO_CFG_PATH])
    assert("nonce" in autotrageur.exchange1_configs)
    assert("nonce" in autotrageur.exchange2_configs)

    if keyfile_loaded:
        assert("apiKey" in autotrageur.exchange1_configs)
        assert("apiKey" in autotrageur.exchange2_configs)
        assert("secret" in autotrageur.exchange1_configs)
        assert("secret" in autotrageur.exchange2_configs)
    else:
        assert("apiKey" not in autotrageur.exchange1_configs)
        assert("apiKey" not in autotrageur.exchange2_configs)
        assert("secret" not in autotrageur.exchange1_configs)
        assert("secret" not in autotrageur.exchange2_configs)


def test_load_db(mocker, autotrageur):
    MOCK_DB_PASSWORD = 'FAKE_DB_PASSWORD'
    mocker.patch('getpass.getpass', return_value=MOCK_DB_PASSWORD)
    mocker.patch.object(db_handler, 'start_db')
    mocker.patch.dict(autotrageur.config, {
        DB_USER: 'test_user',
        DB_NAME: 'test_db'
    })
    mocker.spy(schedule, 'every')

    autotrageur._Autotrageur__load_db()

    getpass.getpass.assert_called_once_with(prompt="Enter database password:")  # pylint: disable=E1101
    db_handler.start_db.assert_called_once_with(        # pylint: disable=E1101
        autotrageur.config[DB_USER],
        MOCK_DB_PASSWORD,
        autotrageur.config[DB_NAME])
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


def test_load_twilio(mocker, autotrageur):
    FAKE_TWILIO_CFG_PATH = 'fake/twilio/cfg/path'
    fake_open = mocker.patch('builtins.open', mocker.mock_open())
    fake_yaml_safe_load = mocker.patch.object(yaml, 'safe_load')
    fake_twilio_client = mocker.Mock()
    fake_twilio_client_constructor = mocker.patch.object(
        bot.arbitrage.autotrageur, 'TwilioClient', return_value=fake_twilio_client)
    fake_test_connection = mocker.patch.object(fake_twilio_client, 'test_connection')
    mocker.patch('os.getenv', return_value='some_env_var')

    autotrageur._Autotrageur__load_twilio(FAKE_TWILIO_CFG_PATH)

    fake_open.assert_called_once_with(FAKE_TWILIO_CFG_PATH, 'r')
    fake_yaml_safe_load.assert_called_once()
    fake_twilio_client_constructor.assert_called_once_with(
        os.getenv('ACCOUNT_SID'), os.getenv('AUTH_TOKEN'))
    fake_test_connection.assert_called_once_with()



@pytest.mark.parametrize("ex1_test", [True, False])
@pytest.mark.parametrize("ex2_test", [True, False])
@pytest.mark.parametrize("dryrun", [True, False])
def test_setup(mocker, autotrageur, ex1_test, ex2_test, dryrun):
    fake_slippage = 0.25
    fake_pair = 'fake/pair'
    placeholder = 'fake'
    trader = mocker.patch('bot.arbitrage.autotrageur.CCXTTrader')
    instance = trader.return_value
    mocker.patch.object(autotrageur, 'exchange1_configs', create=True)
    mocker.patch.object(autotrageur, 'exchange2_configs', create=True)
    configuration = {
        EXCHANGE1_PAIR: fake_pair,
        EXCHANGE2_PAIR: fake_pair,
        EXCHANGE1: placeholder,
        EXCHANGE2: placeholder,
        SLIPPAGE: fake_slippage,
        EXCHANGE1_TEST: ex1_test,
        EXCHANGE2_TEST: ex2_test,
        DRYRUN: dryrun,
        DRYRUN_E1_BASE: 20,
        DRYRUN_E1_QUOTE: 20000,
        DRYRUN_E2_BASE: 20,
        DRYRUN_E2_QUOTE: 20000
    }

    mocker.patch.dict(autotrageur.config, configuration)
    autotrageur._setup()

    # Dry run verification.
    if dryrun:
        assert isinstance(autotrageur.dry_run, DryRun)
        assert isinstance(autotrageur.dry_run.e1, DryRunExchange)
        assert isinstance(autotrageur.dry_run.e2, DryRunExchange)
    else:
        assert autotrageur.dry_run is None

    if ex1_test and ex2_test:
        assert(instance.connect_test_api.call_count == 2)
    elif ex1_test != ex2_test:
        assert(instance.connect_test_api.call_count == 1)
    else:
        assert(instance.connect_test_api.call_count == 0)

    assert(instance.load_markets.call_count == 2)


class TestRunAutotrageur:
    FAKE_ARGS = ['fake', 'arguments']

    def _setup_mocks(self, mocker, autotrageur):
        # Use SystemExit to stop the infinite loop.
        mocker.patch.object(autotrageur, '_alert')
        mocker.patch.object(autotrageur, '_setup')
        mocker.patch.object(autotrageur, '_clean_up', create=True)
        mocker.patch.object(autotrageur, '_execute_trade')
        mocker.patch.object(autotrageur, '_wait', side_effect=[
            None, None, None, None, SystemExit
        ])

    @pytest.mark.parametrize("requires_configs", [True, False])
    def test_run_autotrageur(self, mocker, autotrageur, requires_configs):
        self._setup_mocks(mocker, autotrageur)
        if requires_configs:
            mocker.patch.object(autotrageur, '_load_configs')
        mocker.patch.object(autotrageur, '_poll_opportunity', side_effect=[
            True, True, False, True, False
        ])
        mock_counter = mocker.patch('bot.arbitrage.autotrageur.RetryCounter')
        retry_counter_instance = mock_counter.return_value

        with pytest.raises(SystemExit):
            autotrageur.run_autotrageur(self.FAKE_ARGS, requires_configs)

        autotrageur._alert.assert_not_called()
        autotrageur._setup.assert_called_once_with()
        assert autotrageur._clean_up.call_count == 5
        assert autotrageur._wait.call_count == 5
        assert autotrageur._poll_opportunity.call_count == 5
        assert autotrageur._execute_trade.call_count == 3
        assert retry_counter_instance.increment.call_count == 5

        if requires_configs:
            autotrageur._load_configs.assert_called_with(self.FAKE_ARGS)

    @pytest.mark.parametrize("dryrun", [True, False])
    def test_run_autotrageur_keyboard_interrupt(self, mocker, autotrageur,
                                                dryrun):
        self._setup_mocks(mocker, autotrageur)
        mocker.patch.object(autotrageur, '_load_configs')
        mocker.patch.object(autotrageur, '_poll_opportunity', side_effect=[
            True, True, False, KeyboardInterrupt, False
        ])
        mocker.patch.dict(autotrageur.config, { DRYRUN: dryrun })
        mock_counter = mocker.patch('bot.arbitrage.autotrageur.RetryCounter')
        retry_counter_instance = mock_counter.return_value

        if dryrun:
            mocker.patch.object(autotrageur, 'dry_run', create=True)
            mocker.patch.object(autotrageur.dry_run, 'log_all', create=True)
            autotrageur.run_autotrageur(self.FAKE_ARGS)
        else:
            with pytest.raises(KeyboardInterrupt):
                autotrageur.run_autotrageur(self.FAKE_ARGS)

        autotrageur._alert.assert_not_called()
        autotrageur._setup.assert_called_once_with()
        autotrageur._load_configs.assert_called_with(self.FAKE_ARGS)
        assert autotrageur._clean_up.call_count == 4
        assert autotrageur._wait.call_count == 3
        assert autotrageur._poll_opportunity.call_count == 4
        assert autotrageur._execute_trade.call_count == 2
        assert retry_counter_instance.increment.call_count == 3

        if dryrun:
            autotrageur.dry_run.log_all.assert_called_once_with()

    @pytest.mark.parametrize("exc_type", [
        AuthenticationError,
        ccxt.ExchangeError,
        Exception
    ])
    @pytest.mark.parametrize("dryrun", [True, False])
    def test_run_autotrageur_exception(self, mocker, autotrageur, exc_type,
                                       dryrun):
        self._setup_mocks(mocker, autotrageur)
        mocker.patch.object(autotrageur, '_load_configs')
        mocker.patch.object(autotrageur, '_poll_opportunity', side_effect=[
            True, exc_type, False, True, False
        ])
        mocker.patch.dict(autotrageur.config, { DRYRUN: dryrun })

        if dryrun:
            mocker.patch.object(autotrageur, 'dry_run', create=True)
            with pytest.raises(exc_type):
                autotrageur.run_autotrageur(self.FAKE_ARGS)
            autotrageur._alert.assert_called_once()
        else:
            # Save original function before mocking out `run_autotrageur`
            autotrageur.original_run_autotrageur = autotrageur.run_autotrageur

            mocker.spy(autotrageur, 'original_run_autotrageur')
            mocker.patch.object(autotrageur, 'run_autotrageur')
            mocker.patch.object(autotrageur, 'dry_run', None, create=True)
            autotrageur.original_run_autotrageur(self.FAKE_ARGS)

            autotrageur._alert.assert_called_once()
            assert autotrageur.config[DRYRUN] is True

            # Perhaps redundant checks, but ensures that the two are differentiated.
            autotrageur.original_run_autotrageur.assert_called_once_with(
                self.FAKE_ARGS)
            autotrageur.run_autotrageur.assert_called_once_with(
                self.FAKE_ARGS, False)

        autotrageur._setup.assert_called_once_with()
        autotrageur._load_configs.assert_called_with(self.FAKE_ARGS)
        assert autotrageur._clean_up.call_count == 2
        assert autotrageur._wait.call_count == 1
        assert autotrageur._poll_opportunity.call_count == 2
        assert autotrageur._execute_trade.call_count == 1

    @pytest.mark.parametrize("decrement_returns", [
        [True, True, False], [True, True, True]])
    def test_run_autotrageur_retry_exception(self, mocker, autotrageur,
                                             decrement_returns):
        self._setup_mocks(mocker, autotrageur)
        mocker.patch.object(autotrageur, '_load_configs')
        mocker.patch.object(autotrageur, '_poll_opportunity', side_effect=[
            True, RetryableError, RetryableError, RetryableError, SystemExit
        ])
        mocker.patch.dict(autotrageur.config, {DRYRUN: True})
        mock_counter = mocker.patch('bot.arbitrage.autotrageur.RetryCounter')
        retry_counter_instance = mock_counter.return_value
        retry_counter_instance.decrement.side_effect = decrement_returns

        if decrement_returns[2]:
            # With a third successful retry, the SystemExit side effect
            # on the 5th _poll_opportunity will be triggered.
            with pytest.raises(SystemExit):
                autotrageur.run_autotrageur(self.FAKE_ARGS)

            assert autotrageur._poll_opportunity.call_count == 5
            assert autotrageur._clean_up.call_count == 5
            assert autotrageur._wait.call_count == 4
        else:
            with pytest.raises(RetryableError):
                autotrageur.run_autotrageur(self.FAKE_ARGS)

            assert autotrageur._poll_opportunity.call_count == 4
            assert autotrageur._clean_up.call_count == 4
            assert autotrageur._wait.call_count == 3

        autotrageur._setup.assert_called_once_with()
        autotrageur._load_configs.assert_called_with(self.FAKE_ARGS)
        assert autotrageur._execute_trade.call_count == 1
        assert retry_counter_instance.increment.call_count == 1
