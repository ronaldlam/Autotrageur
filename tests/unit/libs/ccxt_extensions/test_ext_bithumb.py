# pylint: disable=E1101
from decimal import Decimal

import ccxt
import pytest

import libs.ccxt_extensions as ccxt_extensions


BUY = 'buy'
SELL = 'sell'

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
    },
    {
        "info": {
            "status": "0000",
            "order_id": "1529629423655557",
            "data": [
                {
                    "cont_id": "27907430",
                    "units": "0.0",
                    "price": "585500",
                    "total": 0,
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
    },
    {
        "info": {
            "status": "0000",
            "order_id": "1529629537405951",
            "data": [
                {
                    "cont_id": "27907447",
                    "units": "0",
                    "price": "584500",
                    "total": 0,
                    "fee": 0
                }
            ]
        },
        "id": "1529629537405951"
    }
]

BUY_RESULTS = [
    {
        'pre_fee_base': Decimal('0.25'),
        'pre_fee_quote': Decimal('69060'),
        'post_fee_base': Decimal('0.24975'),
        'post_fee_quote': Decimal('69060'),
        'fees': Decimal('0.00025'),
        'fee_asset': 'ETH',
        'price': Decimal('276240'),
        'true_price': Decimal('276516.5165165165165165165165'),
        'side': 'buy',
        'type': 'market',
        'order_id': '1429500241523',
        'extra_info': {}
    },
    {
        'pre_fee_base': Decimal('0.01'),
        'pre_fee_quote': Decimal('5855'),
        'post_fee_base': Decimal('0.01'),
        'post_fee_quote': Decimal('5855'),
        'fees': Decimal('0'),
        'fee_asset': 'ETH',
        'price': Decimal('585500'),
        'true_price': Decimal('585500'),
        'side': 'buy',
        'type': 'market',
        'order_id': '1529629423655557',
        'extra_info': {}
    },
    {
        'pre_fee_base': Decimal('0'),
        'pre_fee_quote': Decimal('0'),
        'post_fee_base': Decimal('0'),
        'post_fee_quote': Decimal('0'),
        'fees': Decimal('0'),
        'fee_asset': 'ETH',
        'price': Decimal('0'),
        'true_price': Decimal('0'),
        'side': 'buy',
        'type': 'market',
        'order_id': '1529629423655557',
        'extra_info': {}
    }
]

SELL_RESULTS = [
    {
        'pre_fee_base': Decimal('1'),
        'pre_fee_quote': Decimal('259891'),
        'post_fee_base': Decimal('1'),
        'post_fee_quote': Decimal('259632'),
        'fees': Decimal('259'),
        'fee_asset': 'KRW',
        'price': Decimal('259891'),
        'true_price': Decimal('259632'),
        'side': 'sell',
        'type': 'market',
        'order_id': '1429500318982',
        'extra_info': {}
    },
    {
        'pre_fee_base': Decimal('0.01'),
        'pre_fee_quote': Decimal('5845'),
        'post_fee_base': Decimal('0.01'),
        'post_fee_quote': Decimal('5845'),
        'fees': Decimal('0'),
        'fee_asset': 'KRW',
        'price': Decimal('584500'),
        'true_price': Decimal('584500'),
        'side': 'sell',
        'type': 'market',
        'order_id': '1529629537405951',
        'extra_info': {}
    },
    {
        'pre_fee_base': Decimal('0'),
        'pre_fee_quote': Decimal('0'),
        'post_fee_base': Decimal('0'),
        'post_fee_quote': Decimal('0'),
        'fees': Decimal('0'),
        'fee_asset': 'KRW',
        'price': Decimal('0'),
        'true_price': Decimal('0'),
        'side': 'sell',
        'type': 'market',
        'order_id': '1529629537405951',
        'extra_info': {}
    }
]


@pytest.fixture(scope='module')
def bithumb():
    return ccxt_extensions.ext_bithumb()


@pytest.mark.parametrize('side, raw_response, result', zip(
    [BUY]*len(BUY_RESPONSES) + [SELL]*len(SELL_RESPONSES),
    BUY_RESPONSES + SELL_RESPONSES,
    BUY_RESULTS + SELL_RESULTS))
def test_create_market_order(mocker, bithumb, side, raw_response, result):
    mocker.patch('ccxt.bithumb.create_market_%s_order' % side,
                 return_value=raw_response)
    response = bithumb._create_market_order(side, 'ETH/KRW', 1)
    if side == BUY:
        assert ccxt.bithumb.create_market_buy_order.called_with(side, 'ETH/KRW', 1)
    if side == SELL:
        assert ccxt.bithumb.create_market_sell_order.called_with(side, 'ETH/KRW', 1)
    assert response['pre_fee_base'] == result['pre_fee_base']
    assert response['pre_fee_quote'] == result['pre_fee_quote']
    assert response['post_fee_base'] == result['post_fee_base']
    assert response['post_fee_quote'] == result['post_fee_quote']
    assert response['fees'] == result['fees']
    assert response['fee_asset'] == result['fee_asset']
    assert response['price'] == result['price']
    assert response['true_price'] == result['true_price']
    assert response['side'] == result['side']
    assert response['type'] == result['type']
    assert response['order_id'] == result['order_id']
    assert response['extra_info'] == result['extra_info']


def test_fail_create_market_order(bithumb):
    with pytest.raises(ccxt.ExchangeError):
        bithumb._create_market_order('not_a_side', 'ETH/KRW', 1)

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
