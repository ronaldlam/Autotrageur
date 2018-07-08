import logging
import time

import ccxt

from bot.common.ccxt_constants import BUY_SIDE
from bot.common.decimal_constants import ZERO, HUNDRED
from libs.utilities import num_to_decimal


OPTIONS = {"options": ["immediate-or-cancel"]}


class ext_gemini(ccxt.gemini):
    """Subclass of ccxt's gemini.py for internal use.

    The name ext_gemini is to keep similar convention when initializing
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

    def _package_result(self, result, symbol, local_timestamp, params):
        """Retrieve Autotrageur specific unified response given the ccxt
        response.

        Example ccxt response for a create_market_sell_order call:
        {
            "info": {
                "order_id": "97546903",
                "id": "97546903",
                "symbol": "ethusd",
                "exchange": "gemini",
                "avg_execution_price": "394.10",
                "side": "sell",
                "type": "exchange limit",
                "timestamp": "1529616497",
                "timestampms": 1529616497632,
                "is_live": False,
                "is_cancelled": False,
                "is_hidden": False,
                "was_forced": False,
                "executed_amount": "0.001",
                "remaining_amount": "0",
                "client_order_id": "1529616491439",
                "options": [
                    "immediate-or-cancel"
                ],
                "price": "388.00",
                "original_amount": "0.001"
            },
            "id": "97546903"
        }
        Example entry in ccxt response list for the fetch_my_trades call:
        {
            "id": "97546905",
            "order": "97546903",
            "info": {
                "price": "394.10",
                "amount": "0.001",
                "timestamp": 1529616497,
                "timestampms": 1529616497632,
                "type": "Sell",
                "aggressor": True,
                "fee_currency": "USD",
                "fee_amount": "0.00098525",
                "tid": 97546905,
                "order_id": "97546903",
                "exchange": "gemini",
                "is_auction_fill": False,
                "client_order_id": "1529616491439"
            },
            "timestamp": 1529616497632,
            "datetime": "2018-06-21T21: 28: 18.632Z",
            "symbol": "ETH/USD",
            "type": None,
            "side": "Sell",
            "price": 394.1,
            "cost": 0.3941,
            "amount": 0.001,
            "fee": {
                "cost": 0.00098525,
                "currency": "USD"
            }
        }
        The result is formatted as:
        {
            'pre_fee_base' (Decimal): 0.100,
            'pre_fee_quote' (Decimal): 50.00,
            'post_fee_base' (Decimal): 0.100,
            'post_fee_quote' (Decimal): 50.50,
            'fees' (Decimal): 0.50,
            'fee_asset' (String): 'USD',
            'price' (Decimal): 500.00,
            'true_price' (Decimal): 495.00,
            'side' (String): 'sell',
            'type' (String): 'limit',
            'order_id' (String): 'RU486',
            'exchange_timestamp' (int): 1529651177,
            'local_timestamp' (int): 1529651177,
            'extra_info' (dict):  { 'options': 'immediate-or-cancel' }
        }

        Args:
            result (dict): The result of the 'create order' call.
            symbol (str): The symbol of the market.
            local_timestamp (int): The local timestamp.
            params (dict): The extra parameters to pass to the ccxt call.

        Returns:
            dict: An Autotrageur specific unified response.
        """
        trade_list = self.fetch_my_trades(symbol)
        order_id = result['id']
        side = result['info']['side']
        _, quote = symbol.upper().split('/')
        trades = list(filter(lambda x: x['order'] == order_id, trade_list))

        pre_fee_base = num_to_decimal(result['info']['executed_amount'])

        pre_fee_quote = ZERO
        fees = ZERO

        # Add up contents of trades
        for trade in trades:
            pre_fee_quote += num_to_decimal(trade['cost'])
            fees += num_to_decimal(trade['fee']['cost'])

        # Calculate post fee numbers.
        post_fee_base = pre_fee_base

        if side == BUY_SIDE:
            post_fee_quote = pre_fee_quote + fees   # Pay additional fees
        else:
            post_fee_quote = pre_fee_quote - fees   # Pay from proceeds

        # Last step is to calculate the prices. We set this to zero if
        # no transaction was made.
        if pre_fee_base == ZERO:
            price = ZERO
            true_price = ZERO
        else:
            price = pre_fee_quote / pre_fee_base
            true_price = post_fee_quote / post_fee_base

        return {
            'pre_fee_base': pre_fee_base,
            'pre_fee_quote': pre_fee_quote,
            'post_fee_base': post_fee_base,
            'post_fee_quote': post_fee_quote,
            'fees': fees,
            'fee_asset': quote,
            'price': price,
            'true_price': true_price,
            'side': side,
            'type': 'limit',
            'order_id': order_id,
            'exchange': self.name.lower(),
            'exchange_timestamp': int(result['info']['timestamp']),
            'local_timestamp': local_timestamp,
            'extra_info': params
        }

    # @Override
    def describe(self):
        """Return gemini exchange object with corrected info.

        The describe() call returns a map of attributes that the
        exchange object contains. The deep_extend() call is defined in
        exchange.py and lets you combine additional details into a given
        map. Thus this simply extends the description of the default
        ccxt.gemini() object.

        NOTE: The taker/maker fees will have to be updated every time a gemini
        account has changed trading fee schedules (tiers).  See
        https://gemini.com/trading-fee-schedule/#maker-vs-taker

        Returns:
            dict: The description of the exchange.
        """
        return self.deep_extend(super().describe(), {
            'has': {
                'createMarketOrder': 'emulated'
            },
            'fees': {
                'trading': {
                    'tierBased': True,
                    'percentage': True,
                    'taker': 0.01,
                    'maker': 0.01,
                },
            },
        })

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
        # See https://docs.gemini.com/rest-api/#symbols-and-minimums
        precision = {
            'BTC/USD': {
                'base': 10,     # The precision of min execution quantity
                'quote': 2,     # The precision of min execution quantity
                'amount': 8,    # The precision of min order increment
                'price': 2,     # The precision of min price increment
            },
            'ETH/USD': {
                'base': 8,
                'quote': 2,
                'amount': 6,
                'price': 2,
            },
            'ETH/BTC': {
                'base': 8,
                'quote': 10,
                'amount': 6,
                'price': 5,
            },
            'ZEC/USD': {
                'base': 8,
                'quote': 2,
                'amount': 6,
                'price': 2,
            },
            'ZEC/BTC': {
                'base': 8,
                'quote': 10,
                'amount': 6,
                'price': 5,
            },
            'ZEC/ETH': {
                'base': 8,
                'quote': 8,
                'amount': 6,
                'price': 4,
            },
        }
        limits = {
            'BTC/USD': {
                'amount': {
                    'min': 0.00001,     # Only min order amounts are specified
                    'max': None,
                },
                'price': {
                    'min': None,
                    'max': None,
                }
            },
            'ETH/USD': {
                'amount': {
                    'min': 0.001,
                    'max': None,
                },
                'price': {
                    'min': None,
                    'max': None,
                }
            },
            'ETH/BTC': {
                'amount': {
                    'min': 0.001,
                    'max': None,
                },
                'price': {
                    'min': None,
                    'max': None,
                }
            },
            'ZEC/USD': {
                'amount': {
                    'min': 0.001,
                    'max': None,
                },
                'price': {
                    'min': None,
                    'max': None,
                }
            },
            'ZEC/BTC': {
                'amount': {
                    'min': 0.001,
                    'max': None,
                },
                'price': {
                    'min': None,
                    'max': None,
                }
            },
            'ZEC/ETH': {
                'amount': {
                    'min': 0.001,
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
            market['precision'] = precision[market['symbol']]
            market['limits'] = limits[market['symbol']]

        return markets

    # @Override
    def prepare_emulated_market_buy_order(
            self, symbol, quote_amount, asset_price, slippage):
        """Calculate data required for the ccxt market buy order.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            quote_amount (Decimal): The amount to buy in quote currency.
            asset_price (Decimal): The target buy price, quote per base.
            slippage (Decimal): The percentage off asset_price the market
                buy will tolerate.

        Returns:
            (Decimal, Decimal): Tuple of asset volume and limit price.
        """
        # Calculated volume of asset expected to be purchased.
        asset_volume = quote_amount / asset_price
        # Maximum price we are willing to pay.
        ratio = (HUNDRED + slippage) / HUNDRED
        limit_price = asset_price * ratio
        a_precision = self.markets[symbol]['precision']['amount']
        p_precision = self.markets[symbol]['precision']['price']

        # Rounding is required for direct ccxt call.
        asset_volume = round(asset_volume, a_precision)
        limit_price = round(limit_price, p_precision)

        logging.info("Gemini emulated market buy.")
        logging.info("Estimated asset price: %s" % asset_price)
        logging.info("Asset volume: %s" % asset_volume)
        logging.info("Limit price: %s" % limit_price)

        return (asset_volume, limit_price)

    # @Override
    def create_emulated_market_buy_order(
            self, symbol, quote_amount, asset_price, slippage):
        """Create an emulated market buy order with maximum slippage.

        This is implemented as an 'immediate or cancel' trade which will
        execute on only immediately available liquidity. If the
        calculated limit price is above the maximum fill price, a market
        order is completed immediately. If the available liquidity is
        not enough for quote_amount of the asset, only fills under the
        limit price will complete and the order will not be completely
        filled.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            quote_amount (Decimal): The amount to buy in quote currency.
            asset_price (Decimal): The target buy price, quote per base.
            slippage (Decimal): The percentage off asset_price the market
                buy will tolerate.

        Returns:
            dict: An Autotrageur specific unified response.
        """
        (asset_volume, limit_price) = self.prepare_emulated_market_buy_order(
            symbol, quote_amount, asset_price, slippage)
        local_timestamp = int(time.time())
        result = self.create_limit_buy_order(
            symbol,
            asset_volume,
            limit_price,
            OPTIONS)
        return self._package_result(result, symbol, local_timestamp, OPTIONS)

    # @Override
    def prepare_emulated_market_sell_order(
            self, symbol, asset_price, asset_amount, slippage):
        """Calculate data required for the ccxt market sell order.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_price (Decimal): The price, quote per base.
            asset_amount (Decimal): The amount of the asset to be sold.
            slippage (Decimal): The percentage off asset_price the market
                buy will tolerate.

        Returns:
            (Decimal, Decimal): Tuple of the rounded asset amount and limit
                price.
        """
        # Minimum price we are willing to sell.
        ratio = (HUNDRED - slippage) / HUNDRED
        a_precision = self.markets[symbol]['precision']['amount']
        p_precision = self.markets[symbol]['precision']['price']
        rounded_amount = round(asset_amount, a_precision)
        rounded_limit_price = round(asset_price * ratio, p_precision)

        logging.info("Gemini emulated market sell.")
        logging.info("Estimated asset price: %s" % asset_price)
        logging.info("Asset volume: %s" % rounded_amount)
        logging.info("Limit price: %s" % rounded_limit_price)

        return (rounded_amount, rounded_limit_price)

    # @Override
    def create_emulated_market_sell_order(
            self, symbol, asset_price, asset_amount, slippage):
        """Create an emulated market sell order with maximum slippage.

        This is implemented as an 'immediate or cancel' trade which will
        execute on only immediately available liquidity. If the
        calculated limit price is below the minimum fill price, a market
        order is completed immediately. If the available liquidity is
        not enough for asset_amount of the asset, only fills over the
        limit price will complete and the order will not be completely
        filled.

        Args:
            symbol (str): The symbol of the market, ie. 'ETH/USD'.
            asset_price (Decimal): The price, quote per base.
            asset_amount (Decimal): The amount of the asset to be sold.
            slippage (Decimal): The percentage off asset_price the market
                buy will tolerate.

        Returns:
            dict: An Autotrageur specific unified response.
        """
        (rounded_amount, rounded_limit_price) = (
            self.prepare_emulated_market_sell_order(
                symbol, asset_price, asset_amount, slippage))
        local_timestamp = int(time.time())
        result = self.create_limit_sell_order(
            symbol,
            rounded_amount,
            rounded_limit_price,
            OPTIONS)
        return self._package_result(result, symbol, local_timestamp, OPTIONS)
