import pytest

from libs.trade.executor.ccxt_executor import CCXTExecutor


def test_constructor(mocker, ext_gemini_exchange):
    executor = CCXTExecutor(ext_gemini_exchange)
    assert(executor.exchange is ext_gemini_exchange)


@pytest.mark.parametrize(
    "symbol, quote_amount, asset_price, slippage", [
        ('ETH/USD', 2, 600, 1),
        ('BTC/USD', 5, 10000, 2)
    ]
)
def test_create_emulated_buy(
        fake_ccxt_executor, ext_gemini_exchange, symbol, quote_amount, asset_price, slippage):
    args = [symbol, quote_amount, asset_price, slippage]
    fake_ccxt_executor.create_emulated_market_buy_order(*args)
    ext_gemini_exchange.create_emulated_market_buy_order.assert_called_once()
    ext_gemini_exchange.create_emulated_market_buy_order.assert_called_with(*args)


@pytest.mark.parametrize(
    "symbol, asset_price, asset_amount, slippage", [
        ('ETH/USD', 600, 1, 1),
        ('BTC/USD', 10000, 2, 2)
    ]
)
def test_create_emulated_sell(
        fake_ccxt_executor, ext_gemini_exchange, symbol, asset_price, asset_amount, slippage):
    args = [symbol, asset_price, asset_amount, slippage]
    fake_ccxt_executor.create_emulated_market_sell_order(*args)
    ext_gemini_exchange.create_emulated_market_sell_order.assert_called_once()
    ext_gemini_exchange.create_emulated_market_sell_order.assert_called_with(*args)


@pytest.mark.parametrize(
    "symbol, asset_amount, asset_price", [
        ('ETH/USD', 5, 600),
        ('BTC/USD', 3, 10000)
    ]
)
def test_create_buy(fake_ccxt_executor, ext_gemini_exchange, symbol, asset_amount, asset_price):
    fake_ccxt_executor.create_market_buy_order(symbol, asset_amount, asset_price)
    ext_gemini_exchange.create_market_buy_order.assert_called_once()
    # asset_price is unused.
    ext_gemini_exchange.create_market_buy_order.assert_called_with(symbol, asset_amount)


@pytest.mark.parametrize(
    "symbol, asset_amount, asset_price", [
        ('ETH/USD', 5, 600),
        ('BTC/USD', 3, 10000)
    ]
)
def test_create_sell(fake_ccxt_executor, ext_gemini_exchange, symbol, asset_amount, asset_price):
    fake_ccxt_executor.create_market_sell_order(symbol, asset_amount, asset_price)
    ext_gemini_exchange.create_market_sell_order.assert_called_once()
    # asset_price is unused.
    ext_gemini_exchange.create_market_sell_order.assert_called_with(symbol, asset_amount)
