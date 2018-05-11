import pytest

import libs.ccxt_extensions as ccxt_extensions


BUY_PARAMS = [
    ('ETH/USD', 10000, 600, 1, 0),
    ('ETH/USD', 10000, 665, 1.6, 1),
    ('ETH/USD', 10000, 665, 1.5, 2),
    ('BTC/USD', 10000, 10000, 0.5, 3),
    ('ETH/USD', 10000, 600, 0, 4),
    pytest.param('ETH/USD', 10000, 0, 1, 5,
        marks=pytest.mark.xfail(strict=True, raises=ZeroDivisionError)),
    ('ETH/USD', 0, 600, 1, 6),
    ('ETH/USD', 10000.41, 600, 1, 7),
    ('ETH/USD', 10000, 665.41, 1.6, 8),
    ('ETH/USD', 10000.51, 665.51, 1.5, 9),
]

SELL_PARAMS = [
    ('ETH/USD', 600, 5, 1, 0),
    ('ETH/USD', 634, 5.3, 1.11, 1),
    ('ETH/USD', 600, 5.12341, 1, 2),
    ('ETH/USD', 600.12, 5, 1, 3),
    ('BTC/USD', 10000, 2, 1.134, 4),
    ('BTC/USD', 12345, 6, 7, 5),
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
        asset_price * ((100.0 + slippage) / 100.0), PRECISION[symbol]['price'])

    return (result_volume, result_price)


@pytest.fixture
def sell_results(request):
    symbol = SELL_PARAMS[request.param][0]
    asset_price = SELL_PARAMS[request.param][1]
    asset_amount = SELL_PARAMS[request.param][2]
    slippage = SELL_PARAMS[request.param][3]

    result_amount = round(asset_amount, PRECISION[symbol]['amount'])
    result_price = round(
        asset_price * ((100.0 - slippage) / 100.0), PRECISION[symbol]['price'])

    return (result_amount, result_price)


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

    gemini.create_emulated_market_buy_order(
        symbol, quote_amount, asset_price, slippage)

    result_volume, result_price = buy_results

    gemini.create_limit_buy_order.assert_called_with(
        symbol,
        result_volume,
        result_price,
        {"options": ["immediate-or-cancel"]})


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

    gemini.create_emulated_market_sell_order(
        symbol, asset_price, asset_amount, slippage)

    result_amount, result_price = sell_results

    gemini.create_limit_sell_order.assert_called_with(
        symbol,
        result_amount,
        result_price,
        {"options": ["immediate-or-cancel"]})


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
    }
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
    }
}
