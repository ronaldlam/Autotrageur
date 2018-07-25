import getpass

import ccxt
import libs.db.maria_db_handler as db_handler
import pytest
import schedule
import yaml
from libs.security.encryption import decrypt
from libs.utilities import keyfile_to_map
from libs.utils.ccxt_utils import RetryableError

import bot.arbitrage.autotrageur
from bot.arbitrage.autotrageur import AuthenticationError, Autotrageur
from bot.common.config_constants import (DB_NAME, DB_USER, DRYRUN,
                                         DRYRUN_E1_BASE, DRYRUN_E1_QUOTE,
                                         DRYRUN_E2_BASE, DRYRUN_E2_QUOTE,
                                         EXCHANGE1, EXCHANGE1_PAIR,
                                         EXCHANGE1_TEST, EXCHANGE2,
                                         EXCHANGE2_PAIR, EXCHANGE2_TEST,
                                         SLIPPAGE)
from bot.trader.dry_run import DryRun, DryRunExchange


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
    fake_yaml = mocker.patch.object(yaml, 'load')
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
    mocker.patch.object(autotrageur, '_Autotrageur__load_keyfile')
    mocker.patch.dict(autotrageur.config, { EXCHANGE1: 'e1', EXCHANGE2: 'e2' })
    if not keyfile_loaded:
        autotrageur._Autotrageur__load_keyfile.return_value = None

    autotrageur._load_configs(args)

    autotrageur._Autotrageur__load_config_file.assert_called_once()
    autotrageur._Autotrageur__load_db.assert_called_once()
    autotrageur._Autotrageur__load_keyfile.assert_called_once()
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

    autotrageur._Autotrageur__load_db()

    getpass.getpass.assert_called_once_with(prompt="Enter database password:")  # pylint: disable=E1101
    db_handler.start_db.assert_called_once_with(        # pylint: disable=E1101
        autotrageur.config[DB_USER],
        MOCK_DB_PASSWORD,
        autotrageur.config[DB_NAME])

@pytest.mark.parametrize("ex1_test", [True, False])
@pytest.mark.parametrize("ex2_test", [True, False])
@pytest.mark.parametrize("client_quote_usd", [True, False])
@pytest.mark.parametrize(
    "balance_check_success, dryrun", [
        (True, True),
        (True, False),
        (False, True),
        (False, False)
    ]
)
def test_setup(
        mocker, autotrageur, ex1_test, ex2_test, client_quote_usd,
        balance_check_success, dryrun):
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

    if client_quote_usd:
        instance.quote = 'USD'
    else:
        # Set a fiat quote pair that is not USD to trigger conversion calls.
        instance.quote = 'KRW'

    mocker.patch.dict(autotrageur.config, configuration)
    mocker.spy(schedule, 'every')

    # If wallet balance fetch fails, expect either AuthenticationError or
    # ExchangeNotAvailable to be thrown.
    if balance_check_success is False and dryrun is False:
        instance.update_wallet_balances.side_effect = ccxt.AuthenticationError()
        with pytest.raises(AuthenticationError):
            autotrageur._setup()
    else:
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

    if client_quote_usd:
        # `conversion_needed` not set in the patched trader instance.
        assert(schedule.every.call_count == 0)          # pylint: disable=E1101
        assert len(schedule.jobs) == 0
        assert(instance.set_forex_ratio.call_count == 0)
    else:
        assert instance.conversion_needed is True
        assert(schedule.every.call_count == 2)          # pylint: disable=E1101
        assert len(schedule.jobs) == 2
        assert(instance.set_forex_ratio.call_count == 2)

    schedule.clear()

    if balance_check_success is False and dryrun is False:
        # Expect called once and encountered exception.
        instance.update_wallet_balances.assert_called_once_with(
            is_dry_run=dryrun)
    else:
        assert(instance.update_wallet_balances.call_count == 2)
        instance.update_wallet_balances.assert_called_with(is_dry_run=dryrun)


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
