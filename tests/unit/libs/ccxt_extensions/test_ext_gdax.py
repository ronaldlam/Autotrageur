from decimal import Decimal

import ccxt
import pytest

import libs.ccxt_extensions as ccxt_extensions


# Test Constants.
FAKE_ORDER_ID = 'SOME_UNIQUE_ID'

BUY_FETCH_ORDER = {
    "id": "082b53ee-4e5a-4383-acd5-b8fb9381e977",
    "info": {
        "id": "082b53ee-4e5a-4383-acd5-b8fb9381e977",
        "size": "0.01000000",
        "product_id": "ETH-USD",
        "side": "buy",
        "funds": "94.5391973000000000",
        "type": "market",
        "post_only": False,
        "created_at": "2018-06-22T05: 54: 33.914806Z",
        "done_at": "2018-06-22T05: 54: 33.931Z",
        "done_reason": "filled",
        "fill_fees": "0.0154383000000000",
        "filled_size": "0.01000000",
        "executed_value": "5.1461000000000000",
        "status": "done",
        "settled": True
    },
    "timestamp": 1529646873914,
    "datetime": "2018-06-22T05:54:34.914Z",
    "lastTradeTimestamp": None,
    "status": "closed",
    "symbol": "ETH/USD",
    "type": "market",
    "side": "buy",
    "price": None,
    "cost": 5.1461,
    "amount": 0.01,
    "filled": 0.01,
    "remaining": 0.0,
    "fee": {
        "cost": 0.0154383,
        "currency": None,
        "rate": None
    }
}

BUY_FETCH_ORDER_NOT_FILLED = {
    "id": "082b53ee-4e5a-4383-acd5-b8fb9381e977",
    "info": {
        "id": "082b53ee-4e5a-4383-acd5-b8fb9381e977",
        "size": "0.00000000",
        "product_id": "ETH-USD",
        "side": "buy",
        "type": "market",
        "post_only": False,
        "status": "done",
        "settled": True
    },
    "timestamp": 1529646873914,
    "datetime": "2018-06-22T05:54:34.914Z",
    "status": "closed",
    "symbol": "ETH/USD",
    "type": "market",
    "side": "buy",
    "price": None,
    "cost": 0.00,
    "amount": 0.00,
    "filled": 0.00,
    "remaining": 0.0,
    "fee": {
        "cost": 0.00,
        "currency": None,
        "rate": None
    }
}

SELL_FETCH_ORDER = {
    "id": "40a3f4b6-ba0b-477b-9dde-eb12bd8d0d5e",
    "info": {
        "id": "40a3f4b6-ba0b-477b-9dde-eb12bd8d0d5e",
        "size": "200.00000000",
        "product_id": "ETH-USD",
        "side": "sell",
        "type": "market",
        "post_only": False,
        "created_at": "2018-06-22T08:07:24.594128Z",
        "done_at": "2018-06-22T08: 07: 24.594Z",
        "done_reason": "filled",
        "fill_fees": "301.5756000000000000",
        "filled_size": "200.00000000",
        "executed_value": "100525.2000000000000000",
        "status": "done",
        "settled": True
    },
    "timestamp": 1529654844594,
    "datetime": "2018-06-22T08: 07: 25.594Z",
    "lastTradeTimestamp": None,
    "status": "closed",
    "symbol": "ETH/USD",
    "type": "market",
    "side": "sell",
    "price": None,
    "cost": 100525.2,
    "amount": 200.0,
    "filled": 200.0,
    "remaining": 0.0,
    "fee": {
        "cost": 301.5756,
        "currency": None,
        "rate": None
    }
}

SELL_FETCH_ORDER_NOT_FILLED = {
    "id": "40a3f4b6-ba0b-477b-9dde-eb12bd8d0d5e",
    "info": {
        "id": "40a3f4b6-ba0b-477b-9dde-eb12bd8d0d5e",
        "size": "0.00000000",
        "product_id": "ETH-USD",
        "side": "sell",
        "type": "market",
        "post_only": False,
        "status": "done",
        "settled": True
    },
    "timestamp": 1529646873914,
    "datetime": "2018-06-22T05:54:34.914Z",
    "status": "closed",
    "symbol": "ETH/USD",
    "type": "market",
    "side": "sell",
    "price": None,
    "cost": 0.00,
    "amount": 0.00,
    "filled": 0.00,
    "remaining": 0.0,
    "fee": {
        "cost": 0.00,
        "currency": None,
        "rate": None
    }
}

INTERMEDIATE_ORDER = {
    "id": "INTERMEDIATE_ORDER_ID",
    "info": {
        "id": "INTERMEDIATE_ORDER_ID",
        "status": "pending",
    }
}

INT_ORDER_WITH_STATUS = (INTERMEDIATE_ORDER, INTERMEDIATE_ORDER['info']['status'])
BUY_ORDER_WITH_STATUS = (BUY_FETCH_ORDER, BUY_FETCH_ORDER['info']['status'])

@pytest.fixture(scope='module')
def gdax():
    return ccxt_extensions.ext_gdax()


def test_describe(gdax):
    gdax.describe()
    trading_key = gdax.fees['trading']

    # Check keys.
    assert 'tierBased' in trading_key
    assert 'percentage' in trading_key
    assert 'taker' in trading_key
    assert 'maker' in trading_key

    # Check values.
    assert trading_key['tierBased'] is True
    assert trading_key['percentage'] is True
    assert trading_key['taker'] == 0.003
    assert trading_key['maker'] == 0.00


def test_fetch_order_and_status(mocker, gdax):
    mocker.patch.object(gdax, 'fetch_order', return_value=BUY_FETCH_ORDER)
    order, order_status = gdax._fetch_order_and_status(FAKE_ORDER_ID)
    assert order is BUY_FETCH_ORDER
    assert order_status is BUY_FETCH_ORDER['info']['status']


@pytest.mark.parametrize("bad_value", [
    {}, None, [], ''
])
def test_fetch_order_and_status_exception(mocker, gdax, bad_value):
    mocker.patch.object(gdax, 'fetch_order', return_value=bad_value)
    with pytest.raises((KeyError, TypeError)):
        gdax._fetch_order_and_status('SOME_UNIQUE_ID')


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
def test_poll_order(mocker, gdax, orders_with_status, expected_calls):
    mocker.patch.object(gdax, '_fetch_order_and_status', side_effect=orders_with_status)
    gdax._poll_order('FAKE_OID')
    assert gdax._fetch_order_and_status.call_count == expected_calls


@pytest.mark.parametrize("fetched_order, expected_response, params", [
    (BUY_FETCH_ORDER, {
        'net_base_amount': Decimal('0.01'),
        'net_quote_amount': Decimal('5.1461'),
        'fees': Decimal('0.0154383'),
        'avg_price': Decimal('514.61'),
    }, {
        'some': 'param'
    }),
    (BUY_FETCH_ORDER_NOT_FILLED, {
        'net_base_amount': Decimal('0.00'),
        'net_quote_amount': Decimal('0.00'),
        'fees': Decimal('0.00'),
        'avg_price': Decimal('0.00'),
    }, {})
])
def test_create_market_buy_order(mocker, gdax, fetched_order, expected_response, params):
    mocker.patch('ccxt.gdax.create_market_buy_order', return_value={
        'id': FAKE_ORDER_ID
    })
    mocker.patch.object(gdax, '_poll_order', return_value=fetched_order)

    response = gdax.create_market_buy_order('ETH/USD', 1, params)
    gdax._poll_order.assert_called_with(FAKE_ORDER_ID)
    assert response['net_base_amount'] == expected_response['net_base_amount']
    assert response['net_quote_amount'] == expected_response['net_quote_amount']
    assert response['fees'] == expected_response['fees']
    assert response['avg_price'] == expected_response['avg_price']
    assert response['side'] == 'buy'
    assert response['type'] == 'market'
    assert response['order_id'] == fetched_order['id']
    assert response['exchange_timestamp'] == int(fetched_order['timestamp'] / 1000)
    assert response['extraInfo'] is params


@pytest.mark.parametrize("fetched_order, expected_response, params", [
    (SELL_FETCH_ORDER, {
        'net_base_amount': Decimal('200'),
        'net_quote_amount': Decimal('100525.2'),
        'fees': Decimal('301.5756'),
        'avg_price': Decimal('502.626'),
    }, {
        'some': 'param'
    }),
    (SELL_FETCH_ORDER_NOT_FILLED, {
        'net_base_amount': Decimal('0.00'),
        'net_quote_amount': Decimal('0.00'),
        'fees': Decimal('0.00'),
        'avg_price': Decimal('0.00'),
    }, {})
])
def test_create_market_sell_order(mocker, gdax, fetched_order, expected_response, params):
    mocker.patch('ccxt.gdax.create_market_buy_order', return_value={
        'id': FAKE_ORDER_ID
    })
    mocker.patch.object(gdax, '_poll_order', return_value=fetched_order)

    response = gdax.create_market_buy_order('ETH/USD', 1, params)
    gdax._poll_order.assert_called_with(FAKE_ORDER_ID)
    assert response['net_base_amount'] == expected_response['net_base_amount']
    assert response['net_quote_amount'] == expected_response['net_quote_amount']
    assert response['fees'] == expected_response['fees']
    assert response['avg_price'] == expected_response['avg_price']
    assert response['side'] == 'sell'
    assert response['type'] == 'market'
    assert response['order_id'] == fetched_order['id']
    assert response['exchange_timestamp'] == int(fetched_order['timestamp'] / 1000)
    assert response['extraInfo'] is params
