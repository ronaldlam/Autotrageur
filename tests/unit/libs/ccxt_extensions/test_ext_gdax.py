from decimal import Decimal
import time

import ccxt
import pytest

from bot.common.ccxt_constants import BUY_SIDE, SELL_SIDE
import libs.ccxt_extensions as ccxt_extensions


# Test Constants.
FAKE_ORDER_ID = 'SOME_UNIQUE_ID'

BUY_FETCH_ORDER_TYPICAL = {
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

SELL_FETCH_ORDER_TYPICAL = {
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

SELL_FETCH_ORDER_RESPONSE = {
    'pre_fee_base': Decimal('200'),
    'pre_fee_quote': Decimal('100826.7756'),
    'post_fee_base': Decimal('200'),
    'post_fee_quote': Decimal('100525.2'),
    'fees': Decimal('301.5756'),
    'price': Decimal('502.626'),
    'true_price': Decimal('504.133878')
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

BUY_FETCH_ORDER_RESPONSE = {
    'pre_fee_base': Decimal('0.01'),
    'pre_fee_quote': Decimal('5.1615383'),
    'post_fee_base': Decimal('0.01'),
    'post_fee_quote': Decimal('5.1461'),
    'fees': Decimal('0.0154383'),
    'price': Decimal('514.61'),
    'true_price': Decimal('516.15383'),
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
    mocker.patch.object(gdax, 'fetch_order', return_value=BUY_FETCH_ORDER_TYPICAL)
    order, order_status = gdax._fetch_order_and_status(FAKE_ORDER_ID)
    assert order is BUY_FETCH_ORDER_TYPICAL
    assert order_status is BUY_FETCH_ORDER_TYPICAL['info']['status']


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
        assert response['extraInfo'] is params

    @pytest.mark.parametrize("side, fetched_order, expected_response", zip(
        [BUY_SIDE] * len(BUY_FETCH_ORDERS) + [SELL_SIDE] * len(SELL_FETCH_ORDERS),
        BUY_FETCH_ORDERS + SELL_FETCH_ORDERS,
        BUY_FETCH_ORDER_RESPONSES + SELL_FETCH_ORDER_RESPONSES
    ))
    def test_create_market_order(self, mocker, gdax, side, fetched_order, expected_response):
        # Mock.
        mocker.spy(time, 'time')

        if side == BUY_SIDE:
            mock_ccxt_market_buy = mocker.patch('ccxt.gdax.create_market_buy_order', return_value={
                'id': FAKE_ORDER_ID
            })
        elif side == SELL_SIDE:
            mock_ccxt_market_sell = mocker.patch('ccxt.gdax.create_market_sell_order', return_value={
                'id': FAKE_ORDER_ID
            })
        else:
            with pytest.raises(ccxt.ExchangeError):
                gdax._create_market_order(side, ETH_USD, FAKE_AMOUNT)

        mocker.patch.object(gdax, '_poll_order', return_value=fetched_order)

        # Call tested function.
        response = gdax._create_market_order(side, ETH_USD, FAKE_AMOUNT, PARAMS_EMPTY)

        # Validate.
        time.time.assert_called_with()          # pylint: disable=E1101
        gdax._poll_order.assert_called_with(FAKE_ORDER_ID)

        if side == BUY_SIDE:
            mock_ccxt_market_buy.assert_called_with(ETH_USD, FAKE_AMOUNT, PARAMS_EMPTY)
        else:
            mock_ccxt_market_sell.assert_called_with(ETH_USD, FAKE_AMOUNT, PARAMS_EMPTY)

        self._validate_response(side, response, expected_response, fetched_order, PARAMS_EMPTY)

    @pytest.mark.parametrize("params", [SAMPLE_PARAM, PARAMS_EMPTY])
    @pytest.mark.parametrize("fetched_order, expected_response",
        zip(BUY_FETCH_ORDERS, BUY_FETCH_ORDER_RESPONSES))
    def test_create_market_buy_order(self, mocker, gdax, fetched_order, expected_response, params):
        mocker.patch('ccxt.gdax.create_market_buy_order', return_value={
            'id': FAKE_ORDER_ID
        })
        mocker.spy(gdax, '_create_market_order')
        mocker.patch.object(gdax, '_poll_order', return_value=fetched_order)

        response = gdax.create_market_buy_order(ETH_USD, FAKE_AMOUNT, params)

        # Check that the amount has been cast to a str for gdax.
        assert isinstance(FAKE_AMOUNT, int)
        gdax._create_market_order.assert_called_with(BUY_SIDE, ETH_USD, str(FAKE_AMOUNT), params)
        gdax._poll_order.assert_called_with(FAKE_ORDER_ID)
        self._validate_response(BUY_SIDE, response, expected_response, fetched_order, params)

    @pytest.mark.parametrize("params", [SAMPLE_PARAM, PARAMS_EMPTY])
    @pytest.mark.parametrize("fetched_order, expected_response",
        zip(SELL_FETCH_ORDERS, SELL_FETCH_ORDER_RESPONSES))
    def test_create_market_sell_order(self, mocker, gdax, fetched_order, expected_response, params):
        mocker.patch('ccxt.gdax.create_market_sell_order', return_value={
            'id': FAKE_ORDER_ID
        })
        mocker.spy(gdax, '_create_market_order')
        mocker.patch.object(gdax, '_poll_order', return_value=fetched_order)

        response = gdax.create_market_sell_order(ETH_USD, FAKE_AMOUNT, params)

        # Check that the amount has been cast to a str for gdax.
        assert isinstance(FAKE_AMOUNT, int)
        gdax._create_market_order.assert_called_with(SELL_SIDE, ETH_USD, str(FAKE_AMOUNT), params)
        gdax._poll_order.assert_called_with(FAKE_ORDER_ID)
        self._validate_response(SELL_SIDE, response, expected_response, fetched_order, params)
