import ccxt
import pytest
import yaml

import bot.arbitrage.autotrageur
from bot.arbitrage.autotrageur import (DRYRUN, EXCHANGE1, EXCHANGE1_PAIR,
                                       EXCHANGE1_TEST, EXCHANGE2,
                                       EXCHANGE2_PAIR, EXCHANGE2_TEST,
                                       SLIPPAGE, TARGET_AMOUNT,
                                       AuthenticationError, Autotrageur)
from libs.security.encryption import decrypt
from libs.utilities import keyfile_to_map


class Mocktrageur(Autotrageur):
    """Mock concrete class. ABC's cannot be instantiated."""

    def _poll_opportunity(self):
        pass

    def _execute_trade(self):
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
    mocker.patch.dict(autotrageur.config, { DRYRUN: dryrun })

    if succeed:
        mocker.patch.object(bot.arbitrage.autotrageur, 'decrypt')
        mocker.patch.object(bot.arbitrage.autotrageur, 'keyfile_to_map')

    key_map = autotrageur._Autotrageur__load_keyfile(args)

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
    mocker.patch.object(autotrageur, '_Autotrageur__load_keyfile')
    mocker.patch.dict(autotrageur.config, { EXCHANGE1: 'e1', EXCHANGE2: 'e2' })
    if not keyfile_loaded:
        autotrageur._Autotrageur__load_keyfile.return_value = None

    autotrageur._load_configs(args)

    autotrageur._Autotrageur__load_config_file.assert_called_once()
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


@pytest.mark.parametrize("ex1_test", [True, False])
@pytest.mark.parametrize("ex2_test", [True, False])
@pytest.mark.parametrize("client_quote_usd", [True, False])
@pytest.mark.parametrize(
    "balance_check, dryrun", [
        (True, True),
        (True, False),
        (False, True),
        pytest.param(False, False,
            marks=pytest.mark.xfail(strict=True, raises=AuthenticationError)),
    ]
)
def test_setup_markets(
        mocker, autotrageur, ex1_test, ex2_test, client_quote_usd,
        balance_check, dryrun):
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
        SLIPPAGE: placeholder,
        TARGET_AMOUNT: placeholder,
        EXCHANGE1_TEST: ex1_test,
        EXCHANGE2_TEST: ex2_test,
        DRYRUN: dryrun
    }

    if client_quote_usd:
        instance.quote = 'USD'
    if not balance_check:
        instance.check_wallet_balances.side_effect = ccxt.AuthenticationError()

    mocker.patch.dict(autotrageur.config, configuration)

    autotrageur._setup_markets()

    if ex1_test and ex2_test:
        assert(instance.connect_test_api.call_count == 2)
    elif ex1_test != ex2_test:
        assert(instance.connect_test_api.call_count == 1)
    else:
        assert(instance.connect_test_api.call_count == 0)

    assert(instance.load_markets.call_count == 2)

    if client_quote_usd:
        assert(instance.set_conversion_needed.call_count == 0)
    else:
        assert(instance.set_conversion_needed.call_count == 2)

    if balance_check:
        assert(instance.check_wallet_balances.call_count == 2)
    else:
        assert(dryrun)
