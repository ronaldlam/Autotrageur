import logging
import time

import ccxt

from bot.common.ccxt_constants import BUY_SIDE, SELL_SIDE
from bot.common.decimal_constants import ZERO
from libs.utilities import num_to_decimal


class ext_kraken(ccxt.kraken):
    """Subclass of ccxt's kraken.py for internal use.

    The name ext_kraken is to keep similar convention when initializing
    the exchange classes.
    """
    # @Override
    def __init__(self, exchange_config={}):
        """Constructor.

        Also sets `buy_target_includes_fee` to False as the trading fees for
        buy orders are charged on top of the buy order.  E.g. $1000 market buy
        order with a 1% fee costs $1010 total.

        NOTE: That Kraken does allow specification of where to apply fees, and
        that the calculations will differ depending on choice, and how the
        market order is placed.  See:

        https://bitcoin.stackexchange.com/questions/43227/how-are-fees-charged-at-kraken
        https://www.kraken.com/help/api#private-user-trading

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
            price = num_to_decimal(order['price'])
            true_price = post_fee_quote / post_fee_base

        return {
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

        while order_status != 'closed':
            logging.info(
                'Order still processing with status: {}'.format(order_status))
            time.sleep(0.1)
            order, order_status = self._fetch_order_and_status(order_id)
        return order

    # @Override
    def describe(self):
        """Return kraken exchange object with corrected info.

        The describe() call returns a map of attributes that the
        exchange object contains. The deep_extend() call is defined in
        exchange.py and lets you combine additional details into a given
        map. Thus this simply extends the description of the default
        ccxt.kraken() object.

        NOTE: The taker/maker fees will have to be updated every time a kraken
        account has changed trading fee schedules (tiers).  Most trading
        pairs have the same fee schedule.  See https://www.kraken.com/help/fees

        Returns:
            dict: The description of the exchange.
        """
        return self.deep_extend(super().describe(), {
            'fees': {
                'trading': {
                    'tierBased': True,
                    'percentage': True,
                    'taker': 0.0026,
                    'maker': 0.0016,
                },
            },
        })

    # @Override
    def create_market_buy_order(self, symbol, asset_amount, params={}):
        """Creates a market buy order.

        Returns a unified response for Autotrageur's purposes.  A sample ccxt
        Kraken response for an order looks like:

        {
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

        We parse out the necessary information and create our own response
        structure.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_amount (Decimal): The base asset amount to be bought.
            params (dict): Extra parameters to be passed to the buy order.

        Returns:
            dict: The order result from the ccxt exchange.
        """
        return self._create_market_order(
            BUY_SIDE, symbol, asset_amount, params)

    # @Override
    def create_market_sell_order(self, symbol, asset_amount, params={}):
        """Creates a market sell order.

        Returns a unified response for Autotrageur's purposes.  A sample ccxt
        Kraken response for an order looks like:

        {
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

        We parse out the necessary information and create our own response
        structure.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_amount (Decimal): The base asset amount to be sold.
            params (dict): Extra parameters to be passed to the sell order.

        Returns:
            dict: The order result from the ccxt exchange.
        """
        return self._create_market_order(
            SELL_SIDE, symbol, asset_amount, params)
