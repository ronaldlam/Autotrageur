import logging
import sys

import ccxt

import bot.currencyconverter as currencyconverter
import libs.ccxt_extensions as ccxt_extensions
from libs.trade.executor.ccxt_executor import CCXTExecutor
from libs.trade.executor.dryrun_executor import DryRunExecutor
from libs.trade.fetcher.ccxt_fetcher import CCXTFetcher
from libs.security.utils import keys_exists

EXTENSION_PREFIX = "ext_"


class OrderbookException(Exception):
    """Exception for orderbook related errors."""
    pass


class ExchangeLimitException(Exception):
    """Exception for exchange limit breaches."""
    pass


class CCXTTrader():
    """CCXT Trader for performing trades."""

    def __init__(self, base, quote, exchange_name, slippage, target_amount,
        exchange_config=None, dry_run=False):
        """Constructor.

        The trading client for interacting with the CCXT library.
        Main responsibilities include:
            1) Fetching real-time data from the specified exchange.
            2) Executing orders against the specified exchange.

        Args:
            base (str): The base (first) token/currency of the exchange
                pair.
            quote (str): The quote (second) token/currency of the
                exchange pair.
            exchange_name (str): Desired exchange to query against.
            slippage (float): Maximum desired slippage from emulated
                market trades.
            target_amount (float): Targeted amount to buy or sell, in
                quote currency.
            exchange_config (dict): The exchange's configuration in
                accordance with the ccxt library for instantiating an
                exchange, ex.
                {
                    "apiKey": [SOME_API_KEY]
                    "secret": [SOME_API_SECRET]
                    "verbose": False,
                }
            dry_run (bool): Whether to perform a dry run or not.  If True,
                trades will be logged, rather than actually executed.
        """
        # Instantiate the CCXT Exchange object, or a custom extended CCXT
        # Exchange object.
        exchange_name = exchange_name.lower()
        if EXTENSION_PREFIX + exchange_name in dir(ccxt_extensions):
            self.ccxt_exchange = getattr(
                ccxt_extensions, EXTENSION_PREFIX + exchange_name)(exchange_config)
        else:
            self.ccxt_exchange = getattr(ccxt, exchange_name)(exchange_config)

        self.base = base
        self.quote = quote
        self.exchange_name = exchange_name
        self.fetcher = CCXTFetcher(self.ccxt_exchange)
        self.executor = DryRunExecutor() if dry_run else CCXTExecutor(self.ccxt_exchange)
        self.slippage = slippage
        self.target_amount = target_amount
        self.conversion_needed = False

    def __check_exchange_limits(self, amount, price):
        """Verify amount and price are within exchange limits.

        Args:
            amount (float): Amount of the base asset to trade.
            price (float): Price of base asset in quote currency.

        Raises:
            ExchangeLimitException: If asset buy amount is outside
                exchange limits.
        """
        symbol = "%s/%s" % (self.base, self.quote)
        limits = self.ccxt_exchange.markets[symbol]['limits']

        if amount is not None and keys_exists(limits, 'amount', 'min'):
            min_limit = limits['amount']['min']
            if min_limit is not None and min_limit > amount:
                raise ExchangeLimitException(
                    "Order amount %s %s less than exchange limit %s %s." % (
                        amount,
                        self.base,
                        min_limit,
                        self.base))
        if amount is not None and keys_exists(limits, 'amount', 'max'):
            max_limit = limits['amount']['max']
            if max_limit is not None and max_limit < amount:
                raise ExchangeLimitException(
                    "Order amount %s %s more than exchange limit %s %s." % (
                        amount,
                        self.base,
                        max_limit,
                        self.base))
        if price is not None and keys_exists(limits, 'price', 'min'):
            min_limit = limits['price']['min']
            if min_limit is not None and min_limit > price:
                raise ExchangeLimitException(
                    "Order price %s %s less than exchange limit %s %s." % (
                        price,
                        self.base,
                        min_limit,
                        self.base))
        if price is not None and keys_exists(limits, 'price', 'max'):
            max_limit = limits['price']['max']
            if max_limit is not None and max_limit < price:
                raise ExchangeLimitException(
                    "Order price %s %s more than exchange limit %s %s." % (
                        price,
                        self.base,
                        max_limit,
                        self.base))

    def __round_exchange_precision(self, market_order, symbol, asset_amount):
        """Rounds the asset amount by a precision provided by the exchange.

        Args:
            market_order (bool or string): Is one of: True, False, 'emulated'
                to specify if market order is supported, not supported,
                or emulated.
            symbol (string): The token pair symbol. E.g. 'ETH/USD'
            asset_amount (float): The amount that is to be rounded.

        Returns:
            float: If precision specified by exchange, the rounded asset amount
                is returned.  Else, the asset amount is returned unchanged.
        """
        if market_order:
            # Rounding is required for direct ccxt call.
            precision = self.ccxt_exchange.markets[symbol]['precision']

            # In the case the exchange supports arbitrary precision.
            if 'amount' in precision and precision['amount'] is not None:
                asset_amount = round(asset_amount, precision['amount'])

        return asset_amount

    def connect_test_api(self):
        """Connect to the test API of the exchange.

        Raises:
            NotImplementedError: There is no test API support.
        """
        if "test" in self.ccxt_exchange.urls:
            self.ccxt_exchange.urls["api"] = self.ccxt_exchange.urls["test"]
        else:
            raise NotImplementedError(
                "Test connection to %s not implemented." %
                self.ccxt_exchange.id)

    def check_wallet_balances(self):
        """Checks the wallet balances of the base and quote currencies on the
        exchange.

        TODO: Should implement some fail-fast mechanism here, if wallet
            balances do not meet a minimum.
        """
        for currency in [self.base, self.quote]:
            balance = self.fetcher.fetch_free_balance(currency)
            logging.log(logging.INFO,
                        "Balance of %s on %s: %s" % (
                            currency,
                            self.exchange_name,
                            balance))

    def execute_market_buy(self, asset_price):
        """Execute a market buy order.

        Args:
            asset_price (float): Target asset price for the trade.

        Raises:
            NotImplementedError: If not implemented.
            ExchangeLimitException: If asset buy amount is outside
                exchange limits.

        Returns:
            dict[dict, int]: Dictionary of response, includes 'info'
                and 'id'. The 'info' includes all raw response contents and
                result['id'] == result['info']['id']
        """
        symbol = "%s/%s" % (self.base, self.quote)
        market_order = self.ccxt_exchange.has['createMarketOrder']
        asset_amount = self.__round_exchange_precision(market_order, symbol,
                                                self.target_amount / asset_price)

        # For 'emulated', We check before rounding which is not strictly
        # correct, but it is likely larger issues are at hand if the error is
        # raised.
        self.__check_exchange_limits(asset_amount, asset_price)

        if market_order is True:
            result = self.executor.create_market_buy_order(symbol, asset_amount)
        elif market_order == 'emulated':
            # Rounding will be deferred to emulated implementation.
            result = self.executor.create_emulated_market_buy_order(
                symbol,
                self.target_amount,
                asset_price,
                self.slippage)
        else:
            raise NotImplementedError(
                "Exchange %s has no market buy functionality." %
                self.ccxt_exchange.id)

        return result

    def execute_market_sell(self, asset_price, asset_amount):
        """Execute a market sell order.

        Args:
            asset_price (float): Target asset price for exchanges with
                no market sell support.
            asset_amount (float): Target amount of the asset to be sold.

        Raises:
            NotImplementedError: If not implemented.
            ExchangeLimitException: If asset buy amount is outside
                exchange limits.

        Returns:
            dict[dict, int]: Dictionary of response, includes 'info'
            and 'id'. The 'info' includes all raw response contents and
            result['id'] == result['info']['id']
        """
        symbol = "%s/%s" % (self.base, self.quote)
        market_order = self.ccxt_exchange.has['createMarketOrder']
        asset_amount = self.__round_exchange_precision(market_order, symbol,
                                                 asset_amount)

        # For 'emulated', We check before rounding which is not strictly
        # correct, but it is likely larger issues are at hand if the error is
        # raised.
        self.__check_exchange_limits(asset_amount, asset_price)

        if market_order is True:
            result = self.executor.create_market_sell_order(
                symbol,
                asset_amount)
        elif market_order == 'emulated':
            result = self.executor.create_emulated_market_sell_order(
                symbol,
                asset_price,
                asset_amount,
                self.slippage)
        else:
            raise NotImplementedError(
                "Exchange %s has no market sell functionality." %
                self.ccxt_exchange.id)

        return result

    def get_full_orderbook(self):
        """Gets the full orderbook (bids and asks) from the exchange."""
        return self.fetcher.get_full_orderbook(self.base, self.quote)

    def get_adjusted_market_price_from_orderbook(self, bids_or_asks):
        """Get market buy or sell price

        Return adjusted market buy or sell price given bids or asks and
        amount to be sold. The market price is adjusted based on orderbook
        depth and the 'target amount' requested at the beginning of the program.

        Input of bids will retrieve market sell
        price; input of asks will retrieve market buy price.

        Args:
            bids_or_asks (list[list(float)]): The bids or asks in the
                form of (price, volume).

        Returns:
            float: Prospective price of a market buy or sell.

        Raises:
            OrderbookException: If the orderbook is not deep enough.
        """
        index = 0
        asset_volume = 0.0
        remaining_amount = self.target_amount

        # Subtract from amount until enough of the order book is eaten up by
        # the trade.
        while remaining_amount > 0.0 and index < len(bids_or_asks):
            remaining_amount -= bids_or_asks[index][0] * bids_or_asks[index][1]
            asset_volume += bids_or_asks[index][1]
            index += 1

        if index == len(bids_or_asks) and remaining_amount > 0.0:
            raise OrderbookException("Order book not deep enough for trade.")

        # Add the zero or negative excess amount to trim off the overshoot
        asset_volume += remaining_amount / bids_or_asks[index - 1][0]

        if not self.conversion_needed:
            return self.target_amount / asset_volume
        else:
            asset_usd_value = currencyconverter.convert_currencies(self.quote,
                'USD', self.target_amount)
            return asset_usd_value / asset_volume

    def load_markets(self):
        """Load the markets of the exchange."""
        self.ccxt_exchange.load_markets()

    def set_conversion_needed(self, flag):
        """Indicates whether a conversion is needed for the quote currency.

        Args:
            flag (bool): True or False depending on whether conversion needed.
        """
        self.conversion_needed = flag
