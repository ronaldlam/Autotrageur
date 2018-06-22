from decimal import Decimal
import pytest

import ccxt

import libs.ccxt_extensions as ccxt_extensions


BUY_RESPONSES = [
    {
        "info": {
            "status": "0000",
            "order_id": "1429500241523",
            "data": [
                {
                    "cont_id": "15364",
                    "units": "0.16789964",
                    "price": "270000",
                    "total": 45333,
                    "fee": "0.00016790"
                },
                {
                    "cont_id": "15365",
                    "units": "0.08210036",
                    "price": "289000",
                    "total": 23727,
                    "fee": "0.00008210"
                }
            ]
        },
        "id": "1429500241523"
    },
    {
        "info": {
            "status": "0000",
            "order_id": "1529629423655557",
            "data": [
                {
                    "cont_id": "27907430",
                    "units": "0.01",
                    "price": "585500",
                    "total": 5855,
                    "fee": 0
                }
            ]
        },
        "id": "1529629423655557"
    }
]

SELL_RESPONSES = [
    {
        "info": {
            "status": "0000",
            "order_id": "1429500318982",
            "data": [
                {
                    "cont_id": "15366",
                    "units": "0.78230769",
                    "price": "260000",
                    "total": 203400,
                    "fee": 203
                },
                {
                    "cont_id": "15367",
                    "units": "0.21769231",
                    "price": "259500",
                    "total": 56491,
                    "fee": 56
                }
            ]
        },
        "id": "1429500318982"
    },
    {
        "info": {
            "status": "0000",
            "order_id": "1529629537405951",
            "data": [
                {
                    "cont_id": "27907447",
                    "units": "0.01",
                    "price": "584500",
                    "total": 5845,
                    "fee": 0
                }
            ]
        },
        "id": "1529629537405951"
    }
]

BUY_RESULTS = [
    {
        'net_base_amount': Decimal('0.24975'),
        'net_quote_amount': Decimal('69060'),
        'fees': Decimal('0.00025'),
        'avg_price': Decimal('276516.5165165165165165165165')
    },
    {
        'net_base_amount': Decimal('0.01'),
        'net_quote_amount': Decimal('5855'),
        'fees': Decimal('0'),
        'avg_price': Decimal('585500')
    }
]

SELL_RESULTS = [
    {
        'net_base_amount': Decimal('1'),
        'net_quote_amount': Decimal('259632'),
        'fees': Decimal('259'),
        'avg_price': Decimal('259632')
    },
    {
        'net_base_amount': Decimal('0.01'),
        'net_quote_amount': Decimal('5845'),
        'fees': Decimal('0'),
        'avg_price': Decimal('584500')
    }
]


@pytest.fixture(scope='module')
def bithumb():
    return ccxt_extensions.ext_bithumb()


@pytest.mark.parametrize('raw_response, result', zip(BUY_RESPONSES, BUY_RESULTS))
def test_create_market_buy(mocker, bithumb, raw_response, result):
    mocker.patch('ccxt.bithumb.create_market_buy_order', return_value=raw_response)
    response = bithumb.create_market_buy_order('ETH/KRW', 1)
    assert ccxt.bithumb.create_market_buy_order.called_with('ETH/KRW', 1)      # pylint: disable=E1101
    assert response['net_base_amount'] == result['net_base_amount']
    assert response['net_quote_amount'] == result['net_quote_amount']
    assert response['fees'] == result['fees']
    assert response['avg_price'] == result['avg_price']
    assert response['side'] == 'buy'


@pytest.mark.parametrize('raw_response, result', zip(SELL_RESPONSES, SELL_RESULTS))
def test_create_market_sell(mocker, bithumb, raw_response, result):
    mocker.patch('ccxt.bithumb.create_market_sell_order', return_value=raw_response)
    response = bithumb.create_market_sell_order('ETH/KRW', 1)
    assert ccxt.bithumb.create_market_sell_order.called_with('ETH/KRW', 1)      # pylint: disable=E1101
    assert response['net_base_amount'] == result['net_base_amount']
    assert response['net_quote_amount'] == result['net_quote_amount']
    assert response['fees'] == result['fees']
    assert response['avg_price'] == result['avg_price']
    assert response['side'] == 'sell'


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
