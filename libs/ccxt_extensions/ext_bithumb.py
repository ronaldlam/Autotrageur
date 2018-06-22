from decimal import Decimal
import logging
import sys
import time

import ccxt
from googletrans import Translator

from bot.common.ccxt_constants import UNIFIED_FUNCTION_NAMES
from libs.utilities import num_to_decimal


ZERO = Decimal('0')


class ext_bithumb(ccxt.bithumb):
    """Subclass of ccxt's bithumb.py for internal use.

    The name ext_bithumb is to keep similar convention when initializing
    the exchange classes.
    """
    def __init__(self, *args, **kwargs):
        """Constructor.

        Initializes the ccxt exchange, and decorates relevant unified functions
        for ccxt.bithumb to translate error messages.
        """
        super().__init__(*args, **kwargs)
        for func_name in UNIFIED_FUNCTION_NAMES:
            if func_name in dir(self):
                ccxt_func = getattr(self, func_name)
                setattr(self, func_name, ext_bithumb.decorate(ccxt_func))

    def _create_market_order(self, side, *args, **kwargs):
        """Create a market buy or sell order.

        Args:
            side (str): Either 'buy' or 'sell'.

        Raises:
            ccxt.ExchangeError: If side is specified incorrectly.

        Returns:
            dict: An Autotrageur specific unified response.
        """
        net_base_amount = ZERO
        net_quote_amount = ZERO
        fees = ZERO
        local_timestamp = time.time()

        if side == 'buy':
            response = super().create_market_buy_order(*args, **kwargs)
        elif side == 'sell':
            response = super().create_market_sell_order(*args, **kwargs)
        else:
            raise ccxt.ExchangeError(
                'Invalid side: %s. Must be "buy" or "sell".' % side)

        # Separate trades are stored in the 'data' list.
        trades = response['info']['data']

        # Add up trade totals first
        for trade in trades:
            net_base_amount += num_to_decimal(trade['units'])
            net_quote_amount += num_to_decimal(trade['total'])
            fees += num_to_decimal(trade['fee'])

        # Bithumb buy fees are taken off base amounts; sell fees off
        # quote amounts
        if side == 'buy':
            net_base_amount -= fees
        else:
            net_quote_amount -= fees

        # Last step is to calculate net average price. We set this to
        # zero if no transaction was made.
        if net_quote_amount == ZERO:
            avg_price = ZERO
        else:
            avg_price = net_quote_amount / net_base_amount

        return {
            'net_base_amount': net_base_amount,
            'net_quote_amount': net_quote_amount,
            'fees': fees,
            'avg_price': avg_price,
            'side': side,
            'type': 'market',
            'order_id': response['id'],
            # Bithumb does not return the timestamp.
            'exchange_timestamp': int(local_timestamp),
            'local_timestamp': int(local_timestamp),
            'extraInfo': {}
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
    def create_market_buy_order(self, *args, **kwargs):
        """Create a market buy order.

        The response is formatted as:
        {
            'net_base_amount' : (Decimal) 0.100,
            'net_quote_amount' : (Decimal) 50.00,
            'fees' : (Decimal) 0.50,
            'avg_price' : (Decimal) 500.00,
            'side' : (String) 'buy',
            'type' : (String) 'limit',
            'order_id' : (String) 'RU486',
            'exchange_timestamp' : (int) 1529651177,
            'local_timestamp' : (int) 1529651177,
            'extraInfo' : (dict)  {'options': 'immediate-or-cancel'}
        }

        Returns:
            dict: An Autotrageur specific unified response.
        """
        return self._create_market_order('buy', *args, **kwargs)

    # @Override
    def create_market_sell_order(self, *args, **kwargs):
        """Create a market sell order.

        The response is formatted as:
        {
            'net_base_amount' : (Decimal) 0.100,
            'net_quote_amount' : (Decimal) 50.00,
            'fees' : (Decimal) 0.50,
            'avg_price' : (Decimal) 500.00,
            'side' : (String) 'sell',
            'type' : (String) 'limit',
            'order_id' : (String) 'RU486',
            'exchange_timestamp' : (int) 1529651177,
            'local_timestamp' : (int) 1529651177,
            'extraInfo' : (dict)  {'options': 'immediate-or-cancel'}
        }

        Returns:
            dict: An Autotrageur specific unified response.
        """
        return self._create_market_order('sell', *args, **kwargs)


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
