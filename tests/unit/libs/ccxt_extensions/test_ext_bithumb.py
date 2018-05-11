import pytest

import libs.ccxt_extensions as ccxt_extensions


@pytest.fixture(scope='module')
def bithumb():
    return ccxt_extensions.ext_bithumb()


def test_fetch_markets(bithumb):
    markets = bithumb.fetch_markets()
    for market in markets:
        if market['symbol'] in PRECISION:
            assert(market['precision'] == PRECISION[market['symbol']])
        if market['symbol'] in LIMITS:
            assert(market['limits'] == LIMITS[market['symbol']])



PRECISION = {
    'BTC/KRW': {
        'base': 8,      # The precision of min execution quantity
        'quote': 0,     # The precision of min execution quantity
        'amount': 4,    # The precision of min order increment
        'price': -3,    # The precision of price in KRW
                        # 1000 KRW increment
    },
    'ETH/KRW': {
        'base': 8,
        'quote': 0,
        'amount': 4,
        'price': -3,    # Actual min increment is 500 KRW
    }
}

LIMITS = {
    'BTC/KRW': {
        'amount': {
            'min': 0.001,
            'max': None,
        },
        'price': {
            'min': None,
            'max': None,
        }
    },
    'ETH/KRW': {
        'amount': {
            'min': 0.01,
            'max': None,
        },
        'price': {
            'min': None,
            'max': None,
        }
    },
}
