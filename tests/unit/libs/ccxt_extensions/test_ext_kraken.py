import copy
import time
from decimal import Decimal

import ccxt
import pytest

import libs.ccxt_extensions as ccxt_extensions
from bot.common.ccxt_constants import BUY_SIDE, SELL_SIDE

# Test Constants.
FAKE_ORDER_ID = 'SOME_UNIQUE_ID'

BUY_FETCH_ORDER_TYPICAL = {
    "info": {
        "id": "OIU2FO-MEPBT-3BAXYI",
        "refid": None,
        "userref": 0,
        "status": "closed",
        "reason": None,
        "opentm": 1529623442.3593,
        "closetm": 1529623442.3687,
        "starttm": 0,
        "expiretm": 0,
        "descr": {
            "pair": "ETHUSD",
            "type": "buy",
            "ordertype": "market",
            "price": "0",
            "price2": "0",
            "leverage": "none",
            "order": "buy 0.02000000 ETHUSD @ market",
            "close": ""
        },
        "vol": "0.02000000",
        "vol_exec": "0.02000000",
        "cost": "10.50",
        "fee": "0.02",
        "price": "525.32",
        "stopprice": "0.00000",
        "limitprice": "0.00000",
        "misc": "",
        "oflags": "fciq",
        "trades": [
            "TMPY3X-3PTI3-T2KMGC"
        ]
    },
    "id": "OIU2FO-MEPBT-3BAXYI",
    "timestamp": 1529623442359,
    "datetime": "2018-06-21T23: 24: 02.359Z",
    "lastTradeTimestamp": None,
    "status": "closed",
    "symbol": "ETH/USD",
    "type": "market",
    "side": "buy",
    "price": 525.32,
    "cost": 10.5,
    "amount": 0.02,
    "filled": 0.02,
    "remaining": 0.0,
    "fee": {
        "cost": 0.02,
        "rate": None,
        "currency": "USD"
    }
}

BUY_FETCH_ORDER_NOT_FILLED = {
    "info": {
        "id": "OIU2FO-MEPBT-3BAXYI",
        "refid": None,
        "userref": 0,
        "status": "closed",
        "reason": None,
        "opentm": 1529623442.3593,
        "closetm": 1529623442.3687,
        "starttm": 0,
        "expiretm": 0,
        "descr": {
            "pair": "ETHUSD",
            "type": "buy",
            "ordertype": "market",
            "price": "0",
            "price2": "0",
            "leverage": "none",
            "order": "buy 0.02000000 ETHUSD @ market",
            "close": ""
        },
        "vol": "0.00",
        "vol_exec": "0.00",
        "cost": "0.00",
        "fee": "0.00",
        "price": "0.00",
        "stopprice": "0.00000",
        "limitprice": "0.00000",
        "misc": "",
        "oflags": "fciq",
        "trades": [
            "TMPY3X-3PTI3-T2KMGC"
        ]
    },
    "id": "OIU2FO-MEPBT-3BAXYI",
    "timestamp": 1529623442359,
    "datetime": "2018-06-21T23: 24: 02.359Z",
    "lastTradeTimestamp": None,
    "status": "closed",
    "symbol": "ETH/USD",
    "type": "market",
    "side": "buy",
    "price": 0.00,
    "cost": 0.00,
    "amount": 0.00,
    "filled": 0.00,
    "remaining": 0.0,
    "fee": {
        "cost": 0.00,
        "rate": None,
        "currency": "USD"
    }
}

SELL_FETCH_ORDER_TYPICAL = {
    "info": {
        "id": "O3WG6W-NGIWV-QQXCGS",
        "refid": None,
        "userref": 0,
        "status": "closed",
        "reason": None,
        "opentm": 1529623440.8575,
        "closetm": 1529623440.88,
        "starttm": 0,
        "expiretm": 0,
        "descr": {
            "pair": "ETHUSD",
            "type": "sell",
            "ordertype": "market",
            "price": "0",
            "price2": "0",
            "leverage": "none",
            "order": "sell 0.02100000 ETHUSD @ market",
            "close": ""
        },
        "vol": "0.02100000",
        "vol_exec": "0.02100000",
        "cost": "11.03",
        "fee": "0.02",
        "price": "525.28",
        "stopprice": "0.00000",
        "limitprice": "0.00000",
        "misc": "",
        "oflags": "fciq",
        "trades": [
            "TVKB7U-X4HUP-XRDGW7"
        ]
    },
    "id": "O3WG6W-NGIWV-QQXCGS",
    "timestamp": 1529623440857,
    "datetime": "2018-06-21T23: 24: 01.857Z",
    "lastTradeTimestamp": None,
    "status": "closed",
    "symbol": "ETH/USD",
    "type": "market",
    "side": "sell",
    "price": 525.28,
    "cost": 11.03,
    "amount": 0.021,
    "filled": 0.021,
    "remaining": 0.0,
    "fee": {
        "cost": 0.02,
        "rate": None,
        "currency": "USD"
    }
}

SELL_FETCH_ORDER_NOT_FILLED = {
    "info": {
        "id": "O3WG6W-NGIWV-QQXCGS",
        "refid": None,
        "userref": 0,
        "status": "closed",
        "reason": None,
        "opentm": 1529623440.8575,
        "closetm": 1529623440.88,
        "starttm": 0,
        "expiretm": 0,
        "descr": {
            "pair": "ETHUSD",
            "type": "sell",
            "ordertype": "market",
            "price": "0",
            "price2": "0",
            "leverage": "none",
            "order": "sell 0.02100000 ETHUSD @ market",
            "close": ""
        },
        "vol": "0.00",
        "vol_exec": "0.00",
        "cost": "0.00",
        "fee": "0.00",
        "price": "0.00",
        "stopprice": "0.00",
        "limitprice": "0.00000",
        "misc": "",
        "oflags": "fciq",
        "trades": [
            "TVKB7U-X4HUP-XRDGW7"
        ]
    },
    "id": "O3WG6W-NGIWV-QQXCGS",
    "timestamp": 1529623440857,
    "datetime": "2018-06-21T23: 24: 01.857Z",
    "lastTradeTimestamp": None,
    "status": "closed",
    "symbol": "ETH/USD",
    "type": "market",
    "side": "sell",
    "price": 0.00,
    "cost": 0.00,
    "amount": 0.00,
    "filled": 0.00,
    "remaining": 0.0,
    "fee": {
        "cost": 0.00,
        "rate": None,
        "currency": "USD"
    }
}

SELL_FETCH_ORDER_RESPONSE = {
    'pre_fee_base': Decimal('0.021'),
    'pre_fee_quote': Decimal('11.03'),
    'post_fee_base': Decimal('0.021'),
    'post_fee_quote': Decimal('11.01'),
    'fees': Decimal('0.02'),
    'price': Decimal('525.28'),
    'true_price': Decimal('524.2857142857142857142857142')
}

SELL_FETCH_ORDER_NOT_FILLED_RESPONSE = {
    'pre_fee_base': Decimal('0.00'),
    'pre_fee_quote': Decimal('0.00'),
    'post_fee_base': Decimal('0.00'),
    'post_fee_quote': Decimal('0.00'),
    'fees': Decimal('0.00'),
    'price': Decimal('0.00'),
    'true_price': Decimal('0.00')
}

BUY_FETCH_ORDER_RESPONSE = {
    'pre_fee_base': Decimal('0.02'),
    'pre_fee_quote': Decimal('10.50'),
    'post_fee_base': Decimal('0.02'),
    'post_fee_quote': Decimal('10.52'),
    'fees': Decimal('0.02'),
    'price': Decimal('525.32'),
    'true_price': Decimal('526'),
}

BUY_FETCH_ORDER_NOT_FILLED_RESPONSE = {
    'pre_fee_base': Decimal('0.00'),
    'pre_fee_quote': Decimal('0.00'),
    'post_fee_base': Decimal('0.00'),
    'post_fee_quote': Decimal('0.00'),
    'fees': Decimal('0.00'),
    'price': Decimal('0.00'),
    'true_price': Decimal('0.00'),
}

FETCH_BALANCE_CCXT_RESPONSE = {
    "info": {
        "ZUSD": "2474.1871",
        "ZCAD": "0.0000",
        "XXBT": "0.0550314800",
        "XETH": "2.1488299200"
    },
    "USD": {
        "free": 2474.1871,
        "used": 0.0,
        "total": 2474.1871
    },
    "CAD": {
        "free": 0.0,
        "used": 0.0,
        "total": 0.0
    },
    "BTC": {
        "free": 0.05503148,
        "used": 0.0,
        "total": 0.05503148
    },
    "ETH": {
        "free": 2.14882992,
        "used": 0.0,
        "total": 2.14882992
    },
    "free": {
        "USD": 2474.1871,
        "CAD": 0.0,
        "BTC": 0.05503148,
        "ETH": 2.14882992
    },
    "used": {
        "USD": 0.0,
        "CAD": 0.0,
        "BTC": 0.0,
        "ETH": 0.0
    },
    "total": {
        "USD": 2474.1871,
        "CAD": 0.0,
        "BTC": 0.05503148,
        "ETH": 2.14882992
    }
}

FETCH_OPEN_ORDERS_OPEN_BUY_RESPONSE = [
    {
        "id": "ODEDJH-37FCN-ULFHRY",
        "info": {
            "id": "ODEDJH-37FCN-ULFHRY",
            "refid": None,
            "userref": 0,
            "status": "open",
            "opentm": 1534378898.7951,
            "starttm": 0,
            "expiretm": 0,
            "descr": {
                "pair": "XBTUSD",
                "type": "buy",
                "ordertype": "limit",
                "price": "3000.0",
                "price2": "0",
                "leverage": "none",
                "order": "buy 0.22100000 XBTUSD @ limit 3000.0",
                "close": ""
            },
            "vol": "0.22100000",
            "vol_exec": "0.00000000",
            "cost": "0.00000",
            "fee": "0.00000",
            "price": "0.00000",
            "stopprice": "0.00000",
            "limitprice": "0.00000",
            "misc": "",
            "oflags": "fciq,post"
        },
        "timestamp": 1534378898795,
        "datetime": "2018-08-16T00: 21: 38.795Z",
        "lastTradeTimestamp": None,
        "status": "open",
        "symbol": "BTC/USD",
        "type": "limit",
        "side": "buy",
        "price": 3000.0,
        "cost": 0.0,
        "amount": 0.221,
        "filled": 0.0,
        "remaining": 0.221,
        "fee": {
            "cost": 0.0,
            "rate": None,
            "currency": "USD"
        }
    }
]

FETCH_OPEN_ORDERS_OPEN_SELL_RESPONSE = [
    {
        "id": "OTA3BA-6EZDT-FJ2YVL",
        "info": {
            "id": "OTA3BA-6EZDT-FJ2YVL",
            "refid": None,
            "userref": 0,
            "status": "open",
            "opentm": 1534898678.2204,
            "starttm": 0,
            "expiretm": 0,
            "descr": {
                "pair": "ETHUSD",
                "type": "sell",
                "ordertype": "limit",
                "price": "1200.00",
                "price2": "0",
                "leverage": "none",
                "order": "sell 0.20000000 ETHUSD @ limit 1200.00",
                "close": ""
            },
            "vol": "0.20000000",
            "vol_exec": "0.00000000",
            "cost": "0.00000",
            "fee": "0.00000",
            "price": "0.00000",
            "stopprice": "0.00000",
            "limitprice": "0.00000",
            "misc": "",
            "oflags": "fciq"
        },
        "timestamp": 1534898678220,
        "datetime": "2018-08-22T00:44:38.220Z",
        "lastTradeTimestamp": None,
        "status": "open",
        "symbol": "ETH/USD",
        "type": "limit",
        "side": "sell",
        "price": 1200.0,
        "cost": 0.0,
        "amount": 0.2,
        "filled": 0.0,
        "remaining": 0.2,
        "fee": {
            "cost": 0.0,
            "rate": None,
            "currency": "USD"
        }
    },
    {
        "id": "OPVHM2-W5RET-NT23DO",
        "info": {
            "id": "OPVHM2-W5RET-NT23DO",
            "refid": None,
            "userref": 0,
            "status": "open",
            "opentm": 1534898619.6447,
            "starttm": 0,
            "expiretm": 0,
            "descr": {
                "pair": "ETHUSD",
                "type": "sell",
                "ordertype": "limit",
                "price": "1000.00",
                "price2": "0",
                "leverage": "none",
                "order": "sell 0.50000000 ETHUSD @ limit 1000.00",
                "close": ""
            },
            "vol": "0.50000000",
            "vol_exec": "0.00000000",
            "cost": "0.00000",
            "fee": "0.00000",
            "price": "0.00000",
            "stopprice": "0.00000",
            "limitprice": "0.00000",
            "misc": "",
            "oflags": "fciq"
        },
        "timestamp": 1534898619644,
        "datetime": "2018-08-22T00:43:39.644Z",
        "lastTradeTimestamp": None,
        "status": "open",
        "symbol": "ETH/USD",
        "type": "limit",
        "side": "sell",
        "price": 1000.0,
        "cost": 0.0,
        "amount": 0.5,
        "filled": 0.0,
        "remaining": 0.5,
        "fee": {
            "cost": 0.0,
            "rate": None,
            "currency": "USD"
        }
    }
]

FETCH_BALANCE_AUTOTRAGEUR_OPEN_BUY_RESPONSE = {
    "info": {
        "ZUSD": "2474.1871",
        "ZCAD": "0.0000",
        "XXBT": "0.0550314800",
        "XETH": "2.1488299200"
    },
    "USD": {
        "free": 1811.1871,
        "used": 663.0,
        "total": 2474.1871
    },
    "CAD": {
        "free": 0.0,
        "used": 0.0,
        "total": 0.0
    },
    "BTC": {
        "free": 0.05503148,
        "used": 0.0,
        "total": 0.05503148
    },
    "ETH": {
        "free": 2.14882992,
        "used": 0.0,
        "total": 2.14882992
    },
    "free": {
        "USD": 1811.1871,
        "CAD": 0.0,
        "BTC": 0.05503148,
        "ETH": 2.14882992
    },
    "used": {
        "USD": 663.0,
        "CAD": 0.0,
        "BTC": 0.0,
        "ETH": 0.0
    },
    "total": {
        "USD": 2474.1871,
        "CAD": 0.0,
        "BTC": 0.05503148,
        "ETH": 2.14882992
    }
}

FETCH_BALANCE_AUTOTRAGEUR_OPEN_SELL_RESPONSE = {
    "info": {
        "ZUSD": "2474.1871",
        "ZCAD": "0.0000",
        "XXBT": "0.0550314800",
        "XETH": "2.1488299200"
    },
    "USD": {
        "free": 2474.1871,
        "used": 0.0,
        "total": 2474.1871
    },
    "CAD": {
        "free": 0.0,
        "used": 0.0,
        "total": 0.0
    },
    "BTC": {
        "free": 0.05503148,
        "used": 0.0,
        "total": 0.05503148
    },
    "ETH": {
        "free": 1.44882992,
        "used": 0.7,
        "total": 2.14882992
    },
    "free": {
        "USD": 2474.1871,
        "CAD": 0.0,
        "BTC": 0.05503148,
        "ETH": 1.44882992
    },
    "used": {
        "USD": 0.0,
        "CAD": 0.0,
        "BTC": 0.0,
        "ETH": 0.7
    },
    "total": {
        "USD": 2474.1871,
        "CAD": 0.0,
        "BTC": 0.05503148,
        "ETH": 2.14882992
    }
}

FETCH_BALANCE_AUTOTRAGEUR_OPEN_BUY_SELL_RESPONSE = {
    "info": {
        "ZUSD": "2474.1871",
        "ZCAD": "0.0000",
        "XXBT": "0.0550314800",
        "XETH": "2.1488299200"
    },
    "USD": {
        "free": 1811.1871,
        "used": 663.0,
        "total": 2474.1871
    },
    "CAD": {
        "free": 0.0,
        "used": 0.0,
        "total": 0.0
    },
    "BTC": {
        "free": 0.05503148,
        "used": 0.0,
        "total": 0.05503148
    },
    "ETH": {
        "free": 1.44882992,
        "used": 0.7,
        "total": 2.14882992
    },
    "free": {
        "USD": 1811.1871,
        "CAD": 0.0,
        "BTC": 0.05503148,
        "ETH": 1.44882992
    },
    "used": {
        "USD": 663.0,
        "CAD": 0.0,
        "BTC": 0.0,
        "ETH": 0.7
    },
    "total": {
        "USD": 2474.1871,
        "CAD": 0.0,
        "BTC": 0.05503148,
        "ETH": 2.14882992
    }
}

BUY_FETCH_ORDERS = [
    BUY_FETCH_ORDER_TYPICAL,
    BUY_FETCH_ORDER_NOT_FILLED
]

SELL_FETCH_ORDERS = [
    SELL_FETCH_ORDER_TYPICAL,
    SELL_FETCH_ORDER_NOT_FILLED
]

BUY_FETCH_ORDER_RESPONSES = [
    BUY_FETCH_ORDER_RESPONSE,
    BUY_FETCH_ORDER_NOT_FILLED_RESPONSE
]

SELL_FETCH_ORDER_RESPONSES = [
    SELL_FETCH_ORDER_RESPONSE,
    SELL_FETCH_ORDER_NOT_FILLED_RESPONSE
]

INTERMEDIATE_ORDER = {
    "id": "INTERMEDIATE_ORDER_ID",
    "info": {
        "id": "INTERMEDIATE_ORDER_ID",
        "status": "pending",
    }
}

SAMPLE_PARAM = {
    'some': 'param'
}

PARAMS_EMPTY = {}

INT_ORDER_WITH_STATUS = (INTERMEDIATE_ORDER, INTERMEDIATE_ORDER['info']['status'])
BUY_ORDER_WITH_STATUS = (BUY_FETCH_ORDER_TYPICAL, BUY_FETCH_ORDER_TYPICAL['info']['status'])

ETH_USD = 'ETH/USD'
FAKE_AMOUNT = 1

@pytest.fixture(scope='module')
def kraken():
    return ccxt_extensions.ext_kraken()


def test_describe(kraken):
    kraken.describe()
    trading_key = kraken.fees['trading']

    # Check keys.
    assert 'tierBased' in trading_key
    assert 'percentage' in trading_key
    assert 'taker' in trading_key
    assert 'maker' in trading_key

    # Check values.
    assert trading_key['tierBased'] is True
    assert trading_key['percentage'] is True
    assert trading_key['taker'] == 0.0026
    assert trading_key['maker'] == 0.0016


def test_fetch_order_and_status(mocker, kraken):
    mocker.patch.object(kraken, 'fetch_order', return_value=BUY_FETCH_ORDER_TYPICAL)
    order, order_status = kraken._fetch_order_and_status(FAKE_ORDER_ID)
    assert order is BUY_FETCH_ORDER_TYPICAL
    assert order_status is BUY_FETCH_ORDER_TYPICAL['info']['status']


@pytest.mark.parametrize("bad_value", [
    {}, None, [], ''
])
def test_fetch_order_and_status_exception(mocker, kraken, bad_value):
    mocker.patch.object(kraken, 'fetch_order', return_value=bad_value)
    with pytest.raises((KeyError, TypeError)):
        kraken._fetch_order_and_status('SOME_UNIQUE_ID')


@pytest.mark.parametrize("orders_with_status, expected_calls", [
    ([
        BUY_ORDER_WITH_STATUS
    ], 1),
    ([
        INT_ORDER_WITH_STATUS,
        BUY_ORDER_WITH_STATUS
    ], 2),
    ([
        INT_ORDER_WITH_STATUS,
        INT_ORDER_WITH_STATUS,
        INT_ORDER_WITH_STATUS,
        INT_ORDER_WITH_STATUS,
        INT_ORDER_WITH_STATUS,
        BUY_ORDER_WITH_STATUS
    ], 6),
    ([
        INT_ORDER_WITH_STATUS,
        BUY_ORDER_WITH_STATUS,
        INT_ORDER_WITH_STATUS,
        INT_ORDER_WITH_STATUS,
        INT_ORDER_WITH_STATUS,
        INT_ORDER_WITH_STATUS,
        INT_ORDER_WITH_STATUS
    ], 2)
])
def test_poll_order(mocker, kraken, orders_with_status, expected_calls):
    mocker.patch.object(kraken, '_fetch_order_and_status', side_effect=orders_with_status)
    kraken._poll_order('FAKE_OID')
    assert kraken._fetch_order_and_status.call_count == expected_calls


class TestCreateMarketOrder:
    def _validate_response(self, side, response, expected_response, fetched_order, params):
        assert response['pre_fee_base'] == expected_response['pre_fee_base']
        assert response['pre_fee_quote'] == expected_response['pre_fee_quote']
        assert response['post_fee_base'] == expected_response['post_fee_base']
        assert response['post_fee_quote'] == expected_response['post_fee_quote']
        assert response['fees'] == expected_response['fees']
        assert response['fee_asset'] == 'USD'
        assert response['price'] == expected_response['price']
        assert response['true_price'] == expected_response['true_price']
        assert response['side'] == side
        assert response['type'] == 'market'
        assert response['order_id'] == fetched_order['id']
        assert response['exchange_timestamp'] == int(fetched_order['timestamp'] / 1000)
        assert response['extra_info'] is params

    @pytest.mark.parametrize("side, fetched_order, expected_response", zip(
        [BUY_SIDE] * len(BUY_FETCH_ORDERS) + [SELL_SIDE] * len(SELL_FETCH_ORDERS),
        BUY_FETCH_ORDERS + SELL_FETCH_ORDERS,
        BUY_FETCH_ORDER_RESPONSES + SELL_FETCH_ORDER_RESPONSES
    ))
    def test_create_market_order(self, mocker, kraken, side, fetched_order, expected_response):
        # Mock.
        mocker.spy(time, 'time')

        if side == BUY_SIDE:
            mock_ccxt_market_buy = mocker.patch('ccxt.kraken.create_market_buy_order', return_value={
                'id': FAKE_ORDER_ID
            })
        elif side == SELL_SIDE:
            mock_ccxt_market_sell = mocker.patch('ccxt.kraken.create_market_sell_order', return_value={
                'id': FAKE_ORDER_ID
            })
        else:
            with pytest.raises(ccxt.ExchangeError):
                kraken._create_market_order(side, ETH_USD, FAKE_AMOUNT)

        mocker.patch.object(kraken, '_poll_order', return_value=fetched_order)

        # Call tested function.
        response = kraken._create_market_order(side, ETH_USD, FAKE_AMOUNT, PARAMS_EMPTY)

        # Validate.
        time.time.assert_called_once()          # pylint: disable=E1101
        kraken._poll_order.assert_called_once_with(FAKE_ORDER_ID)

        if side == BUY_SIDE:
            mock_ccxt_market_buy.assert_called_once_with(ETH_USD, FAKE_AMOUNT, PARAMS_EMPTY)
        else:
            mock_ccxt_market_sell.assert_called_once_with(ETH_USD, FAKE_AMOUNT, PARAMS_EMPTY)

        self._validate_response(side, response, expected_response, fetched_order, PARAMS_EMPTY)

    @pytest.mark.parametrize("params", [SAMPLE_PARAM, PARAMS_EMPTY])
    @pytest.mark.parametrize("fetched_order, expected_response",
        zip(BUY_FETCH_ORDERS, BUY_FETCH_ORDER_RESPONSES))
    def test_create_market_buy_order(self, mocker, kraken, fetched_order, expected_response, params):
        mocker.patch('ccxt.kraken.create_market_buy_order', return_value={
            'id': FAKE_ORDER_ID
        })
        mocker.spy(kraken, '_create_market_order')
        mocker.patch.object(kraken, '_poll_order', return_value=fetched_order)

        response = kraken.create_market_buy_order(ETH_USD, FAKE_AMOUNT, params)

        kraken._create_market_order.assert_called_once_with(BUY_SIDE, ETH_USD, FAKE_AMOUNT, params)
        kraken._poll_order.assert_called_once_with(FAKE_ORDER_ID)
        self._validate_response(BUY_SIDE, response, expected_response, fetched_order, params)

    @pytest.mark.parametrize("params", [SAMPLE_PARAM, PARAMS_EMPTY])
    @pytest.mark.parametrize("fetched_order, expected_response",
        zip(SELL_FETCH_ORDERS, SELL_FETCH_ORDER_RESPONSES))
    def test_create_market_sell_order(self, mocker, kraken, fetched_order, expected_response, params):
        mocker.patch('ccxt.kraken.create_market_sell_order', return_value={
            'id': FAKE_ORDER_ID
        })
        mocker.spy(kraken, '_create_market_order')
        mocker.patch.object(kraken, '_poll_order', return_value=fetched_order)

        response = kraken.create_market_sell_order(ETH_USD, FAKE_AMOUNT, params)

        kraken._create_market_order.assert_called_once_with(SELL_SIDE, ETH_USD, FAKE_AMOUNT, params)
        kraken._poll_order.assert_called_once_with(FAKE_ORDER_ID)
        self._validate_response(SELL_SIDE, response, expected_response, fetched_order, params)


@pytest.mark.parametrize('balances, open_orders, expected_result',
    zip(
        [FETCH_BALANCE_CCXT_RESPONSE] * 4,
        [
            FETCH_OPEN_ORDERS_OPEN_BUY_RESPONSE,
            FETCH_OPEN_ORDERS_OPEN_SELL_RESPONSE,
            FETCH_OPEN_ORDERS_OPEN_BUY_RESPONSE + FETCH_OPEN_ORDERS_OPEN_SELL_RESPONSE,
            []
        ],
        [
            FETCH_BALANCE_AUTOTRAGEUR_OPEN_BUY_RESPONSE,
            FETCH_BALANCE_AUTOTRAGEUR_OPEN_SELL_RESPONSE,
            FETCH_BALANCE_AUTOTRAGEUR_OPEN_BUY_SELL_RESPONSE,
            FETCH_BALANCE_CCXT_RESPONSE
        ]
    )
)
def test_fetch_balance(mocker, kraken, balances, open_orders, expected_result):
    mocker.patch.object(
        ccxt.kraken, 'fetch_balance', return_value=copy.deepcopy(balances))
    mocker.patch.object(
        kraken, 'fetch_open_orders', return_value=open_orders)

    result = kraken.fetch_balance()

    assert result == expected_result
