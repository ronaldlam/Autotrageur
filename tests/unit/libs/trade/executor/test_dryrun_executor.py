from unittest.mock import PropertyMock

import pytest

import libs.ccxt_extensions as ccxt_extensions
from libs.trade.executor.dryrun_executor import DryRunExecutor


@pytest.fixture(scope="module")
def exchange():
    return ccxt_extensions.ext_gemini()


@pytest.fixture(scope="function")
def executor(mocker, exchange):
    # Seems that 'name' is a special attribute and this is (one of?) the
    # only way to do this.
    mocker.patch.object(
        exchange, 'name', new_callable=PropertyMock(return_value='Gemini'))
    return DryRunExecutor(exchange)

@pytest.mark.parametrize(
    "symbol, quote_amount, asset_price, slippage, test_id", [
        pytest.param('ETH/USD', 10000, 600, 1, 0),
        pytest.param('ETH/USD', 0, 600, 1, 1),
        pytest.param('ETH/USD', 10000, 2, 1, 2)
    ]
)
def test_create_emulated_market_buy_order(
        mocker, executor, exchange, symbol, quote_amount, asset_price,
        slippage, test_id):
    mocker.patch.object(exchange, 'prepare_emulated_market_buy_order')
    exchange.prepare_emulated_market_buy_order.return_value = (
        round(quote_amount/asset_price, 6), None)
    result = executor.create_emulated_market_buy_order(
        symbol, quote_amount, asset_price, slippage)
    assert(result == EMULATED_BUY_RESULT[test_id])


@pytest.mark.parametrize(
    "symbol, asset_price, asset_amount, slippage, test_id", [
        pytest.param('ETH/USD', 600, 2, 1, 0),
        pytest.param('ETH/USD', 0, 2, 1, 1),
        pytest.param('ETH/USD', 600, 0, 1, 2),
        pytest.param('ETH/USD', 0, 0, 1, 3)
    ]
)
def test_create_emulated_market_sell_order(
        mocker, executor, exchange, symbol, asset_price, asset_amount,
        slippage, test_id):
    mocker.patch.object(exchange, 'prepare_emulated_market_sell_order')
    exchange.prepare_emulated_market_sell_order.return_value = (
        round(asset_amount, 6), None)
    result = executor.create_emulated_market_sell_order(
        symbol, asset_price, asset_amount, slippage)
    assert(result == EMULATED_SELL_RESULT[test_id])


@pytest.mark.parametrize(
    "symbol, asset_amount, asset_price, test_id", [
        ('ETH/USD', 2, 600, 0),
        (None, None, None, 1)
    ]
)
def test_create_market_buy_order(
        executor, symbol, asset_amount, asset_price, test_id):
    result = executor.create_market_buy_order(
        symbol, asset_amount, asset_price)
    assert(result == RESULT[test_id])


@pytest.mark.parametrize(
    "symbol, asset_amount, asset_price, test_id", [
        ('ETH/USD', 2, 600, 0),
        (None, None, None, 1)
    ]
)
def test_create_market_sell_order(
        executor, symbol, asset_amount, asset_price, test_id):
    result = executor.create_market_sell_order(
        symbol, asset_amount, asset_price)
    assert(result == RESULT[test_id])


EMULATED_BUY_RESULT = [
    {
        "info": {
            "symbol": 'ETH/USD',
            "exchange": 'Gemini',
            "price": 600,
            "executed_amount": round(10000/600, 6),
        },
        "id": "DRYRUN"
    },
    {
        "info": {
            "symbol": 'ETH/USD',
            "exchange": 'Gemini',
            "price": 600,
            "executed_amount": round(0/600, 6),
        },
        "id": "DRYRUN"
    },
    {
        "info": {
            "symbol": 'ETH/USD',
            "exchange": 'Gemini',
            "price": 2,
            "executed_amount": round(10000/2, 6),
        },
        "id": "DRYRUN"
    }
]


EMULATED_SELL_RESULT = [
    {
        "info": {
            "symbol": 'ETH/USD',
            "exchange": 'Gemini',
            "price": 600,
            "executed_amount": round(2, 6),
        },
        "id": "DRYRUN"
    },
    {
        "info": {
            "symbol": 'ETH/USD',
            "exchange": 'Gemini',
            "price": 0,
            "executed_amount": round(2, 6),
        },
        "id": "DRYRUN"
    },
    {
        "info": {
            "symbol": 'ETH/USD',
            "exchange": 'Gemini',
            "price": 600,
            "executed_amount": round(0, 6),
        },
        "id": "DRYRUN"
    },
    {
        "info": {
            "symbol": 'ETH/USD',
            "exchange": 'Gemini',
            "price": 0,
            "executed_amount": round(0, 6),
        },
        "id": "DRYRUN"
    }
]


RESULT = [
    {
        "info": {
            "symbol": 'ETH/USD',
            "exchange": 'Gemini',
            "price": 600,
            "executed_amount": 2,
        },
        "id": "DRYRUN"
    },
    {
        "info": {
            "symbol": None,
            "exchange": 'Gemini',
            "price": None,
            "executed_amount": None,
        },
        "id": "DRYRUN"
    }
]
