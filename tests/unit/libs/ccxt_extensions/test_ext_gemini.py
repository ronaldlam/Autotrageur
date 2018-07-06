import time
from decimal import Decimal

import ccxt
import pytest

from bot.common.decimal_constants import HUNDRED
import libs.ccxt_extensions as ccxt_extensions
from ext_gemini_data import (BUY_RESPONSES, BUY_RESULTS, SELL_RESPONSES,
                             SELL_RESULTS)

BUY = 'buy'
SELL = 'sell'
OPTIONS = {"options": ["immediate-or-cancel"]}

BUY_PARAMS = [
    ('ETH/USD', Decimal('10000'), Decimal('600'), Decimal('1'), 0),
    ('ETH/USD', Decimal('10000'), Decimal('665'), Decimal('1.6'), 1),
    ('ETH/USD', Decimal('10000'), Decimal('665'), Decimal('1.5'), 2),
    ('BTC/USD', Decimal('10000'), Decimal('10000'), Decimal('0.5'), 3),
    ('ETH/USD', Decimal('10000'), Decimal('600'), Decimal('0'), 4),
    pytest.param('ETH/USD', Decimal('10000'), Decimal('0'), Decimal('1'), 5,
        marks=pytest.mark.xfail(strict=True, raises=ZeroDivisionError)),
    ('ETH/USD', Decimal('0'), Decimal('600'), Decimal('1'), 6),
    ('ETH/USD', Decimal('10000.41'), Decimal('600'), Decimal('1'), 7),
    ('ETH/USD', Decimal('10000'), Decimal('665.41'), Decimal('1.6'), 8),
    ('ETH/USD', Decimal('10000.51'), Decimal('665.51'), Decimal('1.5'), 9),
]

SELL_PARAMS = [
    ('ETH/USD', Decimal('600'), Decimal('5'), Decimal('1'), 0),
    ('ETH/USD', Decimal('634'), Decimal('5.3'), Decimal('1.11'), 1),
    ('ETH/USD', Decimal('600'), Decimal('5.12341'), Decimal('1'), 2),
    ('ETH/USD', Decimal('600.12'), Decimal('5'), Decimal('1'), 3),
    ('BTC/USD', Decimal('10000'), Decimal('2'), Decimal('1.134'), 4),
    ('BTC/USD', Decimal('12345'), Decimal('6'), Decimal('7'), 5),
]


@pytest.fixture(scope='module')
def gemini():
    gemini = ccxt_extensions.ext_gemini()
    gemini.load_markets()
    return gemini


@pytest.fixture
def buy_results(request):
    # Guard against xfail's
    if len(BUY_PARAMS[request.param]) != 5:
        return None

    symbol = BUY_PARAMS[request.param][0]
    quote_amount = BUY_PARAMS[request.param][1]
    asset_price = BUY_PARAMS[request.param][2]
    slippage = BUY_PARAMS[request.param][3]

    result_volume = round(
        quote_amount / asset_price, PRECISION[symbol]['amount'])

    # NOTE: The parentheses matter for the ratio calculation here.
    # The third test will fail due to floating point inaccuracies.
    result_price = round(
        asset_price * ((HUNDRED + slippage) / HUNDRED), PRECISION[symbol]['price'])

    return (result_volume, result_price)


@pytest.fixture
def sell_results(request):
    symbol = SELL_PARAMS[request.param][0]
    asset_price = SELL_PARAMS[request.param][1]
    asset_amount = SELL_PARAMS[request.param][2]
    slippage = SELL_PARAMS[request.param][3]

    result_amount = round(asset_amount, PRECISION[symbol]['amount'])
    result_price = round(
        asset_price * ((HUNDRED - slippage) / HUNDRED), PRECISION[symbol]['price'])

    return (result_amount, result_price)


@pytest.mark.parametrize('side, calls, expected_result', zip(
    [BUY]*len(BUY_RESPONSES) + [SELL]*len(SELL_RESPONSES),
    BUY_RESPONSES + SELL_RESPONSES,
    BUY_RESULTS + SELL_RESULTS))
def test_package_result(mocker, gemini, side, calls, expected_result):
    mocker.patch.object(
        gemini, 'fetch_my_trades', return_value=calls['fetch_my_trades'])
    local_timestamp = int(time.time())

    response = gemini._package_result(
        calls['create_order'],
        'ETH/USD',
        local_timestamp,
        OPTIONS)

    gemini.fetch_my_trades.assert_called_with('ETH/USD')
    assert response['local_timestamp'] == local_timestamp
    assert response['pre_fee_base'] == expected_result['pre_fee_base']
    assert response['pre_fee_quote'] == expected_result['pre_fee_quote']
    assert response['post_fee_base'] == expected_result['post_fee_base']
    assert response['post_fee_quote'] == expected_result['post_fee_quote']
    assert response['fees'] == expected_result['fees']
    assert response['fee_asset'] == expected_result['fee_asset']
    assert response['price'] == expected_result['price']
    assert response['true_price'] == expected_result['true_price']
    assert response['side'] == expected_result['side']
    assert response['type'] == expected_result['type']
    assert response['order_id'] == expected_result['order_id']
    assert response['exchange_timestamp'] == expected_result['exchange_timestamp']
    assert response['extra_info'] == expected_result['extra_info']


def test_fetch_markets(gemini):
    for market in gemini.fetch_markets():
        if market['symbol'] in PRECISION:
            assert(market['precision'] == PRECISION[market['symbol']])
        if market['symbol'] in LIMITS:
            assert(market['limits'] == LIMITS[market['symbol']])


def test_describe(gemini):
    assert(gemini.has['createMarketOrder'] == 'emulated')
    assert(gemini.fees['trading']['taker'] == 0.01)
    assert(gemini.fees['trading']['maker'] == 0.01)


@pytest.mark.parametrize(
    "symbol, quote_amount, asset_price, slippage, buy_results",
    BUY_PARAMS,
    indirect=['buy_results']
)
def test_prepare_buy(
        gemini, symbol, quote_amount, asset_price, slippage, buy_results):
    asset_volume, limit_price = gemini.prepare_emulated_market_buy_order(
        symbol, quote_amount, asset_price, slippage)

    result_volume, result_price = buy_results

    assert(result_volume == asset_volume)
    assert(result_price == limit_price)


@pytest.mark.parametrize(
    "symbol, quote_amount, asset_price, slippage, buy_results",
    BUY_PARAMS,
    indirect=['buy_results']
)
def test_emulated_market_buy_order(
        mocker, gemini, symbol, quote_amount, asset_price, slippage,
        buy_results):
    mocker.patch.object(gemini, 'create_limit_buy_order')
    mocker.patch.object(gemini, '_package_result')

    gemini.create_emulated_market_buy_order(
        symbol, quote_amount, asset_price, slippage)

    result_volume, result_price = buy_results

    gemini.create_limit_buy_order.assert_called_with(
        symbol,
        result_volume,
        result_price,
        OPTIONS)
    gemini._package_result.called_once()


@pytest.mark.parametrize(
    "symbol, asset_price, asset_amount, slippage, sell_results",
    SELL_PARAMS,
    indirect=['sell_results']
)
def test_prepare_sell(
        gemini, symbol, asset_price, asset_amount, slippage, sell_results):
    rounded_amount, limit_price = gemini.prepare_emulated_market_sell_order(
        symbol, asset_price, asset_amount, slippage)

    result_amount, result_price = sell_results

    assert(rounded_amount == result_amount)
    assert(limit_price == result_price)


@pytest.mark.parametrize(
    "symbol, asset_price, asset_amount, slippage, sell_results",
    SELL_PARAMS,
    indirect=['sell_results']
)
def test_emulated_market_sell_order(
        mocker, gemini, symbol, asset_price, asset_amount, slippage,
        sell_results):
    mocker.patch.object(gemini, 'create_limit_sell_order')
    mocker.patch.object(gemini, '_package_result')

    gemini.create_emulated_market_sell_order(
        symbol, asset_price, asset_amount, slippage)

    result_amount, result_price = sell_results

    gemini.create_limit_sell_order.assert_called_with(
        symbol,
        result_amount,
        result_price,
        OPTIONS)
    gemini._package_result.called_once()


PRECISION = {
    'BTC/USD': {
        'base': 10,     # The precision of min execution quantity
        'quote': 2,     # The precision of min execution quantity
        'amount': 8,    # The precision of min order increment
        'price': 2,     # The precision of min price increment
    },
    'ETH/USD': {
        'base': 8,
        'quote': 2,
        'amount': 6,
        'price': 2,
    },
    'ETH/BTC': {
        'base': 8,
        'quote': 10,
        'amount': 6,
        'price': 5,
    },
    'ZEC/USD': {
        'base': 8,
        'quote': 2,
        'amount': 6,
        'price': 2,
    },
    'ZEC/BTC': {
        'base': 8,
        'quote': 10,
        'amount': 6,
        'price': 5,
    },
    'ZEC/ETH': {
        'base': 8,
        'quote': 8,
        'amount': 6,
        'price': 4,
    },
}

LIMITS = {
    'BTC/USD': {
        'amount': {
            'min': 0.00001,     # Only min order amounts are specified
            'max': None,
        },
        'price': {
            'min': None,
            'max': None,
        }
    },
    'ETH/USD': {
        'amount': {
            'min': 0.001,
            'max': None,
        },
        'price': {
            'min': None,
            'max': None,
        }
    },
    'ETH/BTC': {
        'amount': {
            'min': 0.001,
            'max': None,
        },
        'price': {
            'min': None,
            'max': None,
        }
    },
    'ZEC/USD': {
        'amount': {
            'min': 0.001,
            'max': None,
        },
        'price': {
            'min': None,
            'max': None,
        }
    },
    'ZEC/BTC': {
        'amount': {
            'min': 0.001,
            'max': None,
        },
        'price': {
            'min': None,
            'max': None,
        }
    },
    'ZEC/ETH': {
        'amount': {
            'min': 0.001,
            'max': None,
        },
        'price': {
            'min': None,
            'max': None,
        }
    },
}
