import logging
import time

import ccxt

from bot.common.ccxt_constants import BUY_SIDE, SELL_SIDE
from bot.common.decimal_constants import ZERO
from libs.utilities import num_to_decimal


class ext_gdax(ccxt.gdax):
    """Subclass of ccxt's gdax.py for internal use.

    The name ext_gdax is to keep similar convention when initializing
    the exchange classes.
    """
    # @Override
    def __init__(self, exchange_config={}):
        """Constructor.

        Also sets `buy_target_includes_fee` to False as the trading fees for
        buy orders are charged on top of the buy order.  E.g. $1000 market buy
        order with a 1% fee costs $1010 total.

        Args:
            exchange_config (dict): The exchange's configuration in
                accordance with the ccxt library for instantiating an
                exchange, ex.
                {
                    "apiKey": [SOME_API_KEY]
                    "secret": [SOME_API_SECRET]
                    "verbose": False,
                }
        """
        super().__init__(exchange_config)
        self.buy_target_includes_fee = False

    def _create_market_order(self, side, symbol, amount, params={}):
        """Create a market buy or sell order.

        Args:
            side (str): Either BUY_SIDE or SELL_SIDE.
            symbol (str): The market symbol, ie. 'ETH/USD'.
            amount (str): The base asset amount to buy or sell.
            params (dict): The extra parameters to pass to the ccxt call.
                Defaults to {}.

        Raises:
            ccxt.ExchangeError: If side is specified incorrectly.

        Returns:
            dict: An Autotrageur specific unified response.
        """
        local_ts = int(time.time())
        base, quote = symbol.upper().split('/')

        if side == BUY_SIDE:
            response = super().create_market_buy_order(symbol, amount, params)
        elif side == SELL_SIDE:
            response = super().create_market_sell_order(symbol, amount, params)
        else:
            raise ccxt.ExchangeError(
                'Invalid side: %s. Must be "buy" or "sell".' % side)

        order_id = response['id']
        order = self._poll_order(order_id)

        logging.info('Raw fetched order response for order_id {}:\n {}'.format(
            order_id, order
        ))

        fees = num_to_decimal(order['fee']['cost'])
        filled = num_to_decimal(order['filled'])
        cost = num_to_decimal(order['cost'])

        # Gdax takes the fees away from the quote.
        fee_asset = symbol.split('/')[1].upper()
        pre_fee_base = filled
        pre_fee_quote = cost
        post_fee_base = filled

        if side == BUY_SIDE:
            post_fee_quote = pre_fee_quote + fees   # Pay additional fees
        else:
            post_fee_quote = pre_fee_quote - fees   # Pay from proceeds

        # Set avg_price to zero if no transaction was made.
        if pre_fee_base == ZERO:
            price = ZERO
            true_price = ZERO
        else:
            price = pre_fee_quote / pre_fee_base
            true_price = post_fee_quote / post_fee_base

        return {
            'exchange': self.name.lower(),
            'base': base,
            'quote': quote,
            'pre_fee_base': pre_fee_base,
            'pre_fee_quote': pre_fee_quote,
            'post_fee_base': post_fee_base,
            'post_fee_quote': post_fee_quote,
            'fees': fees,
            'fee_asset': fee_asset,
            'price': price,
            'true_price': true_price,
            'side': order['side'],
            'type': order['type'],
            'order_id': order['id'],
            'exchange_timestamp': int(order['timestamp'] / 1000),
            'local_timestamp': local_ts,
            'extra_info':  params
        }

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
        $0m - $10m      0.30%       0%
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
            asset_amount (Decimal): The base asset amount to be bought.
            params (dict): Extra parameters to be passed to the buy order.

        Returns:
            dict: The order result from the ccxt exchange.
        """
        return self._create_market_order(
            BUY_SIDE, symbol, str(asset_amount), params)

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
            asset_amount (Decimal): The base asset amount to be sold.
            params (dict): Extra parameters to be passed to the sell order.

        Returns:
            dict: The order result from the ccxt exchange.
        """
        return self._create_market_order(
            SELL_SIDE, symbol, str(asset_amount), params)
