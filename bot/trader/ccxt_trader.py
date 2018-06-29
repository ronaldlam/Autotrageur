from enum import Enum
import logging
import sys

import ccxt

import bot.currencyconverter as currencyconverter
import libs.ccxt_extensions as ccxt_extensions
from libs.trade.executor.ccxt_executor import CCXTExecutor
from libs.trade.executor.dryrun_executor import DryRunExecutor
from libs.trade.fetcher.ccxt_fetcher import CCXTFetcher
from libs.utilities import keys_exists, num_to_decimal

EXTENSION_PREFIX = "ext_"


class MarketOrderType(Enum):
    """An Enum for Market order types.

    Args:
        Enum (str): One of: 'buy' or 'sell'.
    """
    BUY = 'buy',
    SELL = 'sell'

    @classmethod
    def has_value(cls, value):
        """Checks if a value is in the MarketOrderType Enum.

        Args:
            value (str): A string value to check against the MarketOrderType
                Enum.

        Returns:
            bool: True if value belongs in MarketOrderType Enum. Else, false.
        """
        return any(value.lower() == item.value for item in cls)


class InvalidMarketOrderTypeError(Exception):
    """Exception thrown when invalid or unspecified MarketOrderType."""
    pass


class OrderbookException(Exception):
    """Exception for orderbook related errors."""
    pass


class ExchangeLimitException(Exception):
    """Exception for exchange limit breaches."""
    pass


class NoForexQuoteException(Exception):
    """Exception when requiring a forex quote target but none present."""
    pass


class CCXTTrader():
    """CCXT Trader for performing trades."""

    def __init__(self, base, quote, exchange_name, slippage,
        exchange_config={}, dry_run=False):
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
            slippage (Decimal): Maximum desired slippage from emulated
                market trades.
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
        self.executor = DryRunExecutor(self.ccxt_exchange) if dry_run else \
            CCXTExecutor(self.ccxt_exchange)
        self.slippage = slippage

        # Initialized variables not from config.
        self.quote_target_amount = num_to_decimal(0.0)
        self.conversion_needed = False
        self.forex_ratio = None

        if dry_run:
            self.base_bal = num_to_decimal(0.0)
            self.quote_bal = num_to_decimal(0.0)

    def __calc_vol_by_book(self, orders, quote_target_amount):
        """Calculates the asset volume with which to execute a trade.

        Uses data from the orderbook to calculate the base asset volume
        to fulfill the quote_target_amount.

        Args:
            orders (list[list(float)]): The bids or asks in the
                form of (price, volume).
            quote_target_amount (Decimal): Targeted amount to buy or
                sell, in quote currency.

        Raises:
            OrderbookException: If the orderbook is not deep enough.

        Returns:
            Decimal: The base asset volume required to fulfill
                target_amount via the orderbook.
        """
        index = 0
        base_asset_volume = num_to_decimal(0.0)
        remaining_amount = quote_target_amount
        ZERO = num_to_decimal(0.0)

        # The decimal orders.
        d_orders = []
        for entry in orders:
            d_orders.append(
                [num_to_decimal(entry[0]), num_to_decimal(entry[1])])

        # Subtract from amount until enough of the order book is eaten up by
        # the trade.
        while remaining_amount > ZERO and index < len(d_orders):
            remaining_amount -= d_orders[index][0] * d_orders[index][1]
            base_asset_volume += d_orders[index][1]
            index += 1

        if index == len(d_orders) and remaining_amount > ZERO:
            raise OrderbookException("Order book not deep enough for trade.")

        # Add the zero or negative excess amount to trim off the overshoot
        base_asset_volume += remaining_amount / d_orders[index - 1][0]

        return base_asset_volume

    def __check_exchange_limits(self, amount, price):
        """Verify amount and price are within exchange limits.

        Args:
            amount (Decimal): Amount of the base asset to trade.
            price (Decimal): Price of base asset in quote currency.

        Raises:
            ExchangeLimitException: If asset buy amount is outside
                exchange limits.
        """
        symbol = "%s/%s" % (self.base, self.quote)
        limits = self.ccxt_exchange.markets[symbol]['limits']

        for measure in [ ('amount', amount), ('price', price) ]:
            for range_limit in ['min', 'max']:
                if (measure[1] and keys_exists(limits, measure[0],
                                               range_limit)):
                    limit = num_to_decimal(limits[measure[0]][range_limit])
                    if limit:
                        if range_limit == 'min' and limit > measure[1]:
                            raise ExchangeLimitException(
                            "Order %s %s %s less than exchange limit %s %s."
                                % (measure[0], measure[1], self.base, limit,
                                   self.base))
                        elif range_limit == 'max' and limit < measure[1]:
                            raise ExchangeLimitException(
                            "Order %s %s %s more than exchange limit %s %s."
                                % (measure[0], measure[1], self.base, limit,
                                   self.base))

    def __round_exchange_precision(self, market_order, symbol, asset_amount):
        """Rounds the asset amount by a precision provided by the exchange.

        Args:
            market_order (bool or string): Is one of: True, False,
                'emulated' to specify if market order is supported, not
                supported, or emulated.
            symbol (string): The token pair symbol. E.g. 'ETH/USD'
            asset_amount (Decimal): The amount that is to be rounded.

        Returns:
            Decimal: If precision specified by exchange, the rounded
                asset amount is returned.  Else, the asset amount is
                returned unchanged.
        """
        if market_order is True:
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

    def fetch_wallet_balances(self):
        """Fetches and saves the wallet balances of the base and quote
        currencies on the exchange.

        Note that quote balances are in USD.

        TODO: Should send an alert here, if wallet balances are 0 for both.
        """
        self.base_bal, self.quote_bal = self.fetcher.fetch_free_balances(
            self.base, self.quote)
        if self.conversion_needed:
            self.quote_bal /= self.forex_ratio
        logging.log(logging.INFO,
                    "%s balances:\n"
                    "%s: %s\n"
                    "%s: %s\n" % (
                        self.exchange_name,
                        self.base,
                        self.base_bal,
                        self.quote,
                        self.quote_bal))

    def execute_market_buy(self, asset_price):
        """Execute a market buy order.

        Args:
            asset_price (Decimal): Target asset price for the trade.

        Raises:
            NotImplementedError: If not implemented.
            ExchangeLimitException: If asset buy amount is outside
                exchange limits.

        Returns:
            dict[dict, int]: Dictionary of response, includes 'info'
                and 'id'. The 'info' includes all raw response contents
                and result['id'] == result['info']['id']
        """
        symbol = "%s/%s" % (self.base, self.quote)
        market_order = self.ccxt_exchange.has['createMarketOrder']
        quote_target_amount = self.quote_target_amount
        asset_amount = quote_target_amount / asset_price

        # If the buy target does not include fees, we want to deduct the fees
        # from the original quote_target_amount. Since the price per unit base
        # is always a fixed price, we can divide by the fee ratio to get both
        # the true target asset_amount and quote_target_amount. Note that all
        # exchanges MUST implement buy_target_includes_fee.
        if self.ccxt_exchange.buy_target_includes_fee is False:
            fee_ratio = num_to_decimal(1) + self.get_taker_fee()
            asset_amount /= fee_ratio
            quote_target_amount /= fee_ratio

        asset_amount = self.__round_exchange_precision(
            market_order, symbol, asset_amount)

        # For 'emulated', We check before rounding which is not strictly
        # correct, but it is likely larger issues are at hand if the error is
        # raised.
        self.__check_exchange_limits(asset_amount, asset_price)

        if market_order is True:
            result = self.executor.create_market_buy_order(
                symbol, asset_amount, asset_price)
        elif market_order == 'emulated':
            # Rounding will be deferred to emulated implementation.
            result = self.executor.create_emulated_market_buy_order(
                symbol,
                quote_target_amount,
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
            asset_price (Decimal): Target asset price for exchanges with
                no market sell support.
            asset_amount (Decimal): Target amount of the asset to be sold.

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
                asset_amount,
                asset_price)
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

        Input of bids will retrieve market sell price; input of asks will
        retrieve market buy price.

        Args:
            bids_or_asks (list[list(float)]): The bids or asks in the
                form of (price, volume).

        Raises:
            OrderbookException: If the orderbook is not deep enough.

        Returns:
            Decimal: Prospective price of a market buy or sell.
        """
        if self.conversion_needed:
            if self.forex_ratio is None:
                 raise NoForexQuoteException("Inaccurate target for orderbook."
                    "  Set a forex ratio.")
            target_amount = self.forex_ratio * self.quote_target_amount
        else:
            target_amount = self.quote_target_amount

        asset_volume = self.__calc_vol_by_book(bids_or_asks, target_amount)
        return self.quote_target_amount / asset_volume

    def get_taker_fee(self):
        """Obtains the exchange's takers fee.

        Raises:
            NotImplementedError: If not accessible through ccxt.

        Returns:
            Decimal: The taker fee, given as a ratio.
        """
        return self.fetcher.fetch_taker_fees()

    def load_markets(self):
        """Load the markets of the exchange."""
        self.ccxt_exchange.load_markets()

    def set_forex_ratio(self):
        """Get foreign currency per USD.

        `forex_quote_target` is set when the quote currency is not USD.
        """
        self.forex_ratio = currencyconverter.convert_currencies(
            'USD', self.quote, num_to_decimal(1))
        logging.info("forex_ratio set to {}".format(self.forex_ratio))
