from decimal import Decimal
import logging
import sys
import time

import ccxt
from googletrans import Translator

from bot.common.ccxt_constants import UNIFIED_FUNCTION_NAMES, BUY_SIDE, SELL_SIDE
from bot.common.decimal_constants import ZERO
from libs.utilities import num_to_decimal, split_symbol


class ext_bithumb(ccxt.bithumb):
    """Subclass of ccxt's bithumb.py for internal use.

    The name ext_bithumb is to keep similar convention when initializing
    the exchange classes.
    """
    def __init__(self, *args, **kwargs):
        """Constructor.

        Initializes the ccxt exchange, and decorates relevant unified
        functions for ccxt.bithumb to translate error messages. Also
        sets 'buy_target_includes_fee'. Bithumb fees are taken off the
        asset that is being bought into, so the buy target indeed
        includes the fee.
        """
        super().__init__(*args, **kwargs)
        for func_name in UNIFIED_FUNCTION_NAMES:
            if func_name in dir(self):
                ccxt_func = getattr(self, func_name)
                setattr(self, func_name, ext_bithumb.decorate(ccxt_func))
        self.buy_target_includes_fee = True

    def _create_market_order(self, side, symbol, amount, params={}):
        """Create a market buy or sell order.

        The ccxt responses for both create_market_buy_order and
        create_market_sell_order have the following format, where the
        'data' array can have multiple entries:
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

        Args:
            side (str): Either BUY_SIDE or SELL_SIDE.
            symbol (str): The market symbol, ie. 'ETH/KRW'.
            amount (str): The base asset amount.
            params (dict): The extra parameters to pass to the ccxt call.

        Raises:
            ccxt.ExchangeError: If side is specified incorrectly.

        Returns:
            dict: An Autotrageur specific unified response.
        """
        pre_fee_base = ZERO
        pre_fee_quote = ZERO
        fees = ZERO
        base, quote = split_symbol(symbol)
        local_timestamp = int(time.time())

        if side == BUY_SIDE:
            response = super().create_market_buy_order(symbol, amount, params)
        elif side == SELL_SIDE:
            response = super().create_market_sell_order(symbol, amount, params)
        else:
            raise ccxt.ExchangeError(
                'Invalid side: %s. Must be "buy" or "sell".' % side)

        # Separate trades are stored in the 'data' list.
        trades = response['info']['data']

        # Add up trade totals first
        for trade in trades:
            pre_fee_base += num_to_decimal(trade['units'])
            pre_fee_quote += num_to_decimal(trade['total'])
            fees += num_to_decimal(trade['fee'])

        # Bithumb buy fees are taken off base amounts; sell fees off
        # quote amounts
        if side == BUY_SIDE:
            post_fee_base = pre_fee_base - fees
            post_fee_quote = pre_fee_quote
            fee_asset = base
        else:
            post_fee_base = pre_fee_base
            post_fee_quote = pre_fee_quote - fees
            fee_asset = quote

        # Last step is to calculate the prices. We set this to zero if
        # no transaction was made.
        if pre_fee_base == ZERO:
            price = ZERO
            true_price = ZERO
        else:
            price = pre_fee_quote / pre_fee_base
            true_price = post_fee_quote / post_fee_base

        return {
            'exchange': self.name.lower(),          # pylint: disable=E1101
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
            'side': side,
            'type': 'market',
            'order_id': response['id'],
            # Bithumb does not return the timestamp.
            'exchange_timestamp': local_timestamp,
            'local_timestamp': local_timestamp,
            'extra_info': params
        }

    @staticmethod
    def decorate(func):
        """Decorator for unified ccxt functions.

        Args:
            func (function): The unified ccxt function to decorate.

        Returns:
            function: The wrapped ccxt function with a translated error
                message.
        """
        def wrapped_unified_func(*args, **kwargs):
            """Wraps a unified ccxt function.

            Returns:
                object: The return value of func.  Can be of arbitrary type or
                    None.
            """
            try:
                ret = func(*args, **kwargs)
            except Exception as exc:
                t = Translator()
                decoded = exc.args[0].encode('utf-8').decode('unicode_escape')
                translation = t.translate(decoded)
                raise type(exc)(translation.text).with_traceback(
                    sys.exc_info()[2])
            else:
                if ret:
                    return ret

        return wrapped_unified_func

    # @Override
    def describe(self):
        """Return bithumb exchange object with corrected info.

        The describe() call returns a map of attributes that the
        exchange object contains. The deep_extend() call is defined in
        exchange.py and lets you combine additional details into a given
        map. Thus this simply extends the description of the default
        ccxt.bithumb() object.

        Returns:
            dict: The description of the exchange.
        """
        return self.deep_extend(super().describe(), {
            'fees': {
                'trading': {
                    'tierBased': True,
                    'percentage': True,
                    'taker': 0.0015,    # Without coupon.
                    'maker': 0.0015,
                },
            },
        })

    # @Override
    def create_market_buy_order(self, symbol, amount, params={}):
        """Create a market buy order.

        The response is formatted as:
        {
            'exchange' (String): 'bithumb',
            'base' (String): 'ETH',
            'quote' (String): 'USD',
            'pre_fee_base' (Decimal): 0.100,
            'pre_fee_quote' (Decimal): 50.00,
            'post_fee_base' (Decimal): 0.100,
            'post_fee_quote' (Decimal): 50.50,
            'fees' (Decimal): 0.50,
            'fee_asset' (String): 'USD',
            'price' (Decimal): 500.00,
            'true_price' (Decimal): 495.00,
            'side' (String): SELL_SIDE,
            'type' (String): 'limit',
            'order_id' (String): 'RU486',
            'exchange_timestamp' (int): 1529651177,
            'local_timestamp' (int): 1529651177,
            'extra_info' (dict):  { 'options': 'immediate-or-cancel' }
        }

        Args:
            symbol (str): The market symbol, ie. 'ETH/KRW'.
            amount (str): The base asset amount.
            params (dict): The extra parameters to pass to the ccxt call.

        Returns:
            dict: An Autotrageur specific unified response.
        """
        return self._create_market_order(BUY_SIDE, symbol, amount, params)

    # @Override
    def create_market_sell_order(self, symbol, amount, params={}):
        """Create a market sell order.

        The response is formatted as:
        {
            'exchange' (String): 'bithumb',
            'base' (String): 'ETH',
            'quote' (String): 'USD',
            'pre_fee_base' (Decimal): 0.100,
            'pre_fee_quote' (Decimal): 50.00,
            'post_fee_base' (Decimal): 0.100,
            'post_fee_quote' (Decimal): 50.50,
            'fees' (Decimal): 0.50,
            'fee_asset' (String): 'USD',
            'price' (Decimal): 500.00,
            'true_price' (Decimal): 495.00,
            'side' (String): SELL_SIDE,
            'type' (String): 'limit',
            'order_id' (String): 'RU486',
            'exchange_timestamp' (int): 1529651177,
            'local_timestamp' (int): 1529651177,
            'extra_info' (dict):  { 'options': 'immediate-or-cancel' }
        }

        Args:
            symbol (str): The market symbol, ie. 'ETH/KRW'.
            amount (str): The base asset amount.
            params (dict): The extra parameters to pass to the ccxt call.

        Returns:
            dict: An Autotrageur specific unified response.
        """
        return self._create_market_order(SELL_SIDE, symbol, amount, params)


    # @Override
    def fetch_markets(self):
        """Retrieve data for the markets of the exchange.

        This gets called by load_markets() which dynamically fetches and
        populates information about a given exchange. Precision and
        limit data is added here for consistency. The ccxt.binance()
        module was used for reference.

        Returns:
            dict: The description of available markets on the exchange.
        """
        # See tests/exploratory/test_bithumb_errors.py
        precision = {
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
        limits = {
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

        markets = super().fetch_markets()

        for market in markets:
            if market['symbol'] in precision:
                market['precision'] = precision[market['symbol']]
            if market['symbol'] in limits:
                market['limits'] = limits[market['symbol']]

        return markets
