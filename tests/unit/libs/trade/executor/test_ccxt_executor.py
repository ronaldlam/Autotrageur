import pytest

from libs.trade.executor.ccxt_executor import CCXTExecutor
import libs.ccxt_extensions as ccxt_extensions

@pytest.fixture(scope='module')
def exchange():
    return ccxt_extensions.ext_gemini()


@pytest.fixture(scope='function')
def executor(mocker, exchange):
    mocker.patch.object(exchange, 'create_emulated_market_buy_order')
    mocker.patch.object(exchange, 'create_emulated_market_sell_order')
    mocker.patch.object(exchange, 'create_market_buy_order')
    mocker.patch.object(exchange, 'create_market_sell_order')
    return CCXTExecutor(exchange)


def test_constructor(mocker, exchange):
    executor = CCXTExecutor(exchange)
    assert(executor.exchange is exchange)


@pytest.mark.parametrize(
    "symbol, quote_amount, asset_price, slippage", [
        ('ETH/USD', 2, 600, 1),
        ('BTC/USD', 5, 10000, 2)
    ]
)
def test_create_emulated_buy(
        executor, exchange, symbol, quote_amount, asset_price, slippage):
    args = [symbol, quote_amount, asset_price, slippage]
    executor.create_emulated_market_buy_order(*args)
    exchange.create_emulated_market_buy_order.assert_called_once()
    exchange.create_emulated_market_buy_order.assert_called_with(*args)


@pytest.mark.parametrize(
    "symbol, asset_price, asset_amount, slippage", [
        ('ETH/USD', 600, 1, 1),
        ('BTC/USD', 10000, 2, 2)
    ]
)
def test_create_emulated_sell(
        executor, exchange, symbol, asset_price, asset_amount, slippage):
    args = [symbol, asset_price, asset_amount, slippage]
    executor.create_emulated_market_sell_order(*args)
    exchange.create_emulated_market_sell_order.assert_called_once()
    exchange.create_emulated_market_sell_order.assert_called_with(*args)


@pytest.mark.parametrize(
    "symbol, asset_amount, asset_price", [
        ('ETH/USD', 5, 600),
        ('BTC/USD', 3, 10000)
    ]
)
def test_create_buy(executor, exchange, symbol, asset_amount, asset_price):
    executor.create_market_buy_order(symbol, asset_amount, asset_price)
    exchange.create_market_buy_order.assert_called_once()
    # asset_price is unused.
    exchange.create_market_buy_order.assert_called_with(symbol, asset_amount)


@pytest.mark.parametrize(
    "symbol, asset_amount, asset_price", [
        ('ETH/USD', 5, 600),
        ('BTC/USD', 3, 10000)
    ]
)
def test_create_sell(executor, exchange, symbol, asset_amount, asset_price):
    executor.create_market_sell_order(symbol, asset_amount, asset_price)
    exchange.create_market_sell_order.assert_called_once()
    # asset_price is unused.
    exchange.create_market_sell_order.assert_called_with(symbol, asset_amount)
