from decimal import Decimal

import ccxt
import pytest

import fp_libs.ccxt_extensions as ccxt_extensions
from fp_libs.trade.fetcher.ccxt_fetcher import CCXTFetcher
from fp_libs.trade.executor.ccxt_executor import CCXTExecutor
from fp_libs.trade.executor.dryrun_executor import DryRunExecutor
from fp_libs.utilities import set_autotrageur_decimal_context
from autotrageur.bot.trader.ccxt_trader import CCXTTrader


# Set the Decimal context before test runs.
set_autotrageur_decimal_context()

# ------------------ Constants fixtures ---------------------------------------
@pytest.fixture(scope='session')
def symbols():
    return {
        'bitcoin': 'BTC',
        'ethereum': 'ETH',
        'usd': 'USD'
    }


@pytest.fixture(scope='session')
def exc_names():
    return {
        'binance': 'binance'
    }

# ------------------ Mock exchange fixtures -----------------------------------
@pytest.fixture()
def fake_binance(mocker, exc_names):
    fake_binance_exchange = mocker.patch.object(ccxt, exc_names['binance'], autospec=True)

    # Fake exchange fees.
    fake_binance_exchange.fees = {
        'trading': {
            'maker': 0.25,
            'taker': 0.10
        }
    }

    # Fake account balances.
    fake_binance_exchange.balances = {
        'BTC': {
            'free': 1.50,
            'used': 2.00,
            'total': 3.50,
        },
        'USD': {
            'free': 123.00,
            'used': 456.00,
            'total': 579.00,
        }
    }

    return fake_binance_exchange


@pytest.fixture(scope='module')
def ext_gemini_exchange():
    return ccxt_extensions.ext_gemini()

# ------------------ Mock fetcher fixtures ------------------------------------
@pytest.fixture()
def ccxtfetcher_binance(mocker, fake_binance):
    return CCXTFetcher(fake_binance)


# ------------------ Mock executor fixtures -----------------------------------
@pytest.fixture()
def fake_ccxt_executor(mocker, ext_gemini_exchange):
    mocker.patch.object(ext_gemini_exchange, 'create_emulated_market_buy_order')
    mocker.patch.object(ext_gemini_exchange, 'create_emulated_market_sell_order')
    mocker.patch.object(ext_gemini_exchange, 'create_market_buy_order')
    mocker.patch.object(ext_gemini_exchange, 'create_market_sell_order')
    return CCXTExecutor(ext_gemini_exchange)


@pytest.fixture()
def fake_dryrun_executor(mocker, ext_gemini_exchange):
    mocker.patch.object(ext_gemini_exchange, 'create_emulated_market_buy_order')
    mocker.patch.object(ext_gemini_exchange, 'create_emulated_market_sell_order')
    mocker.patch.object(ext_gemini_exchange, 'create_market_buy_order')
    mocker.patch.object(ext_gemini_exchange, 'create_market_sell_order')
    fake_fetcher = mocker.Mock()
    fake_dryrun_exchange = mocker.Mock()
    return DryRunExecutor(
        ext_gemini_exchange, fake_fetcher, fake_dryrun_exchange)

# ------------------ Mock trader fixtures -------------------------------------
@pytest.fixture()
def fake_ccxt_trader(mocker, symbols, exc_names, ccxtfetcher_binance, fake_ccxt_executor):
    mocker.patch('fp_libs.trade.fetcher.ccxt_fetcher.CCXTFetcher', return_value=ccxtfetcher_binance)
    mocker.patch('fp_libs.trade.executor.ccxt_executor.CCXTExecutor', return_value=fake_ccxt_executor)
    return CCXTTrader(symbols['bitcoin'], symbols['usd'], exc_names['binance'], Decimal('3.0'), Decimal('20000.0'))
