import ccxt
import pytest

import libs.ccxt_extensions as ccxt_extensions
from libs.trade.fetcher.ccxt_fetcher import CCXTFetcher
from libs.trade.executor.ccxt_executor import CCXTExecutor
from libs.trade.executor.dryrun_executor import DryRunExecutor
from bot.trader.ccxt_trader import CCXTTrader


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
    mocker.patch.object(CCXTFetcher, 'fetch_free_balance')
    mocker.patch.object(CCXTFetcher, 'get_full_orderbook')
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
    return DryRunExecutor(ext_gemini_exchange)

# ------------------ Mock trader fixtures -------------------------------------
@pytest.fixture()
def fake_ccxt_trader(mocker, symbols, exc_names, ccxtfetcher_binance, fake_ccxt_executor):
    mocker.patch('libs.trade.fetcher.ccxt_fetcher.CCXTFetcher', return_value=ccxtfetcher_binance)
    mocker.patch('libs.trade.executor.ccxt_executor.CCXTExecutor', return_value=fake_ccxt_executor)
    return CCXTTrader(symbols['bitcoin'], symbols['usd'], exc_names['binance'], 3.0, 20000.0)
