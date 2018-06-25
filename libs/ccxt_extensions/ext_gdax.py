import logging
import time

import ccxt

from libs.utilities import num_to_decimal


ZERO = num_to_decimal('0')

class ext_gdax(ccxt.gdax):
    """Subclass of ccxt's gdax.py for internal use.

    The name ext_gdax is to keep similar convention when initializing
    the exchange classes.
    """
    # def _create_market_order(self, side, symbol, asset_amount, params={}):

    def _fetch_order_and_status(self, order_id):
        """Fetches the status of the desired order and the order
        response itself.

        Args:
            order_id (str): The unique identifier for the order to fetch.

        Returns:
            (dict, str): The order response and the order response as a tuple.
        """
        order = self.fetch_order(order_id)
        order_status = order['info']['status']
        return order, order_status

    def _poll_order(self, order_id):
        """Polls the desired order until the status is returned as 'done'.

        Args:
            order_id (str): The unique identifier for the order to fetch.

        Returns:
            dict: The desired order response with a status of 'done'.
        """
        order, order_status = self._fetch_order_and_status(order_id)

        while order_status != 'done':
            logging.info(
                'Order still processing with status: {}'.format(order_status))
            time.sleep(0.1)
            order, order_status = self._fetch_order_and_status(order_id)
        return order

    # @Override
    def describe(self):
        """Return gdax exchange object with corrected info.

        The describe() call returns a map of attributes that the
        exchange object contains. The deep_extend() call is defined in
        exchange.py and lets you combine additional details into a given
        map. Thus this simply extends the description of the default
        ccxt.gdax() object.

        NOTE: The taker/maker fees will have to be updated every time a gdax
        account has changed trading fee schedules (tiers).  See
        https://www.gdax.com/fees

        PRICING TIER    TAKER FEE   MAKER FEE
        $0m - $10m	    0.30%       0%
        $10m - $100m    0.20%       0%
        $100m+          0.10%       0%

        Returns:
            dict: The description of the exchange.
        """
        return self.deep_extend(super().describe(), {
            'fees': {
                'trading': {
                    'tierBased': True,
                    'percentage': True,
                    'taker': 0.003,
                    'maker': 0.00,
                },
            },
        })

    # @Override
    def create_market_buy_order(self, symbol, asset_amount, params={}):
        """Creates a market buy order.

        Returns a unified response for Autotrageur's purposes.  A sample ccxt
        GDAX response for an order looks like:

        {
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

        We parse out the necessary information and create our own response
        structure.

        NOTE: asset_amount is cast into a string to be compatible with ccxt
        and GDAX.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_amount (Decimal): The amount of asset to be bought.
            params (dict): Extra parameters to be passed to the buy order.

        Returns:
            dict: The order result from the ccxt exchange.
        """
        local_ts = int(time.time())
        ccxt_resp = super().create_market_buy_order(
            symbol, str(asset_amount), params)
        order_id = ccxt_resp['id']

        order = self._poll_order(order_id)
        logging.info('Raw fetched order response for order_id {}:\n {}'.format(
            order_id, order
        ))

        net_base_amount = num_to_decimal(order['filled'])
        net_quote_amount = num_to_decimal(order['cost'])
        fees = num_to_decimal(order['fee']['cost'])

        # Set avg_price to zero if no transaction was made.
        if net_base_amount == ZERO:
            avg_price = ZERO
        else:
            avg_price = net_quote_amount / net_base_amount

        return {
            'net_base_amount': net_base_amount,
            'net_quote_amount': net_quote_amount,
            'fees': fees,
            'avg_price': avg_price,
            'side': order['side'],
            'type': order['type'],
            'order_id': order['id'],
            'exchange_timestamp': int(order['timestamp'] / 1000),
            'local_timestamp': local_ts,
            'extraInfo':  params
        }

    # @Override
    def create_market_sell_order(self, symbol, asset_amount, params={}):
        """Creates a market sell order.

        Returns a unified response for Autotrageur's purposes.  A sample ccxt
        GDAX response for an order looks like:

        {
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

        We parse out the necessary information and create our own response
        structure.

        NOTE: asset_amount is cast into a string to be compatible with ccxt
        and GDAX.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_amount (Decimal): The amount of asset to be sold.
            params (dict): Extra parameters to be passed to the sell order.

        Returns:
            dict: The order result from the ccxt exchange.
        """
        local_ts = int(time.time())
        ccxt_resp = super().create_market_sell_order(
            symbol, str(asset_amount), params)
        order_id = ccxt_resp['id']

        order = self._poll_order(order_id)
        logging.info('Raw fetched order response for order_id {}:\n {}'.format(
            order_id, order
        ))

        net_base_amount = num_to_decimal(order['filled'])
        net_quote_amount = num_to_decimal(order['cost'])
        fees = num_to_decimal(order['fee']['cost'])

        # Set avg_price to zero if no transaction was made.
        if net_base_amount == ZERO:
            avg_price = ZERO
        else:
            avg_price = net_quote_amount / net_base_amount

        return {
            'net_base_amount': net_base_amount,
            'net_quote_amount': net_quote_amount,
            'fees': fees,
            'avg_price': avg_price,
            'side': order['side'],
            'type': order['type'],
            'order_id': order['id'],
            'exchange_timestamp': int(order['timestamp'] / 1000),
            'local_timestamp': local_ts,
            'extraInfo':  params
        }
