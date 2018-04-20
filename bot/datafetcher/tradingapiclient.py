import logging
import sys

import ccxt

from .baseapiclient import BaseAPIClient
import libs.ccxt_extensions as ccxt_extensions
from libs.security.utils import keys_exists

EXTENSION_PREFIX = "ext_"


class OrderbookException(Exception):
    """Exception for orderbook related errors."""
    pass


class ExchangeLimitException(Exception):
    """Exception for exchange limit breaches."""
    pass


class TradingClient(BaseAPIClient):
    """API Client for real-time data."""

    def __init__(
            self,
            base,
            quote,
            exchange,
            slippage,
            target_amount,
            exchange_config=None):
        """Constructor.

        Fetches real-time data from the specified exchange.

        Args:
            base (str): The base (first) token/currency of the exchange
                pair.
            quote (str): The quote (second) token/currency of the
                exchange pair.
            exchange (str): Desired exchange to query against.
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

        """
        super(TradingClient, self).__init__(base, quote, exchange)
        exchange = exchange.lower()
        if EXTENSION_PREFIX + exchange in dir(ccxt_extensions):
            self.ccxt_exchange = getattr(
                ccxt_extensions, EXTENSION_PREFIX + exchange)(exchange_config)
        else:
            self.ccxt_exchange = getattr(ccxt, exchange)(exchange_config)
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
            and 'id'. The 'info' includes all response contents and
            result['id'] == result['info']['id']
        """
        symbol = "%s/%s" % (self.base, self.quote)
        market_order = self.ccxt_exchange.has['createMarketOrder']
        asset_amount = self.target_amount / asset_price

        if market_order is True:
            # Rounding is required for direct ccxt call.
            precision = self.ccxt_exchange.markets[symbol]['precision']

            # In the case the exchange supports arbitrary precision.
            if 'amount' in precision and precision['amount'] is not None:
                asset_amount = round(asset_amount, precision['amount'])

            self.__check_exchange_limits(asset_amount, asset_price)
            result = self.ccxt_exchange.create_market_buy_order(
                symbol,
                asset_amount)
        elif market_order == 'emulated':
            # We check before rounding which is not strictly correct,
            # but it is likely larger issues are at hand if the error is
            # raised.
            self.__check_exchange_limits(asset_amount, asset_price)
            # Rounding is deferred to emulated implementation.
            result = self.ccxt_exchange.create_emulated_market_buy_order(
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
            and 'id'. The 'info' includes all response contents and
            result['id'] == result['info']['id']
        """
        symbol = "%s/%s" % (self.base, self.quote)
        market_order = self.ccxt_exchange.has['createMarketOrder']

        if market_order is True:
            precision = self.ccxt_exchange.markets[symbol]['precision']

            if 'amount' in precision and precision['amount'] is not None:
                asset_amount = round(asset_amount, precision['amount'])

            self.__check_exchange_limits(asset_amount, asset_price)
            result = self.ccxt_exchange.create_market_sell_order(
                symbol,
                asset_amount)
        elif market_order == 'emulated':
            # We check before rounding which is not strictly correct,
            # but it is likely larger issues are at hand if the error is
            # raised.
            self.__check_exchange_limits(asset_amount, asset_price)
            result = self.ccxt_exchange.create_emulated_market_sell_order(
                symbol,
                asset_price,
                asset_amount,
                self.slippage)
        else:
            raise NotImplementedError(
                "Exchange %s has no market sell functionality." %
                self.ccxt_exchange.id)

        return result

    def fetch_maker_fees(self):
        """Retrieve maker fees for given exchange.

        This function assumes worst case fees. For example, Gemini has a
        volume adjusted fee schedule that will benefit high volume
        traders. This is not accessible through their API and only post-
        trade fees can be retrieved. Information may be loaded per
        exchange in the Autotrageur project extending ccxt. See
        libs.ccxt_extensions.at_gemini for an example.

        Raises:
            NotImplementedError: If not accessible through ccxt.

        Returns:
            float: The maker fee, given as a ratio.
        """
        if self.ccxt_exchange.fees["trading"]["maker"]:
            return self.ccxt_exchange.fees["trading"]["maker"]
        else:
            logging.error(
                "Maker fees should be verified for %s" % self.ccxt_exchange.id)
            raise NotImplementedError("Manually verify fees please.")

    def fetch_taker_fees(self):
        """Retrieve taker fees for given exchange.

        This function assumes worst case fees. High volume discounts are
        not counted. See fetch_maker_fees() for additional details.

        Raises:
            NotImplementedError: If not accessible through ccxt.

        Returns:
            float: The taker fee, given as a ratio.
        """
        if self.ccxt_exchange.fees["trading"]["taker"]:
            return self.ccxt_exchange.fees["trading"]["taker"]
        else:
            logging.error(
                "Taker fees should be verified for %s" % self.ccxt_exchange.id)
            raise NotImplementedError("Manually verify fees please.")

    def fetch_free_balance(self, asset):
        """Fetch balance of the given asset in the account.

        Args:
            asset (string): The balance of the given asset

        Returns:
            float: The balances of the given asset.
        """
        balance = self.ccxt_exchange.fetch_balance()
        return balance[asset]["free"]

    def fetch_last_price(self):
        """Fetches the last transacted price of the token pair.

        Returns:
            int: The last transacted price of the token pair.
        """
        pairsequence = (self.base, "/", self.quote)
        ticker = self.ccxt_exchange.fetch_ticker(''.join(pairsequence))
        return str(ticker['last'])

    def get_full_orderbook(self):
        """Gets the full orderbook (bids and asks) from the exchange."""
        return self.ccxt_exchange.fetch_order_book(
            self.base + "/" + self.quote)

    def get_market_price_from_orderbook(self, bids_or_asks):
        """Get market buy or sell price

        Return potential market buy or sell price given bids or asks and
        amount to be sold. Input of bids will retrieve market sell
        price; input of asks will retrieve market buy price.

        Args:
            bids_or_asks (list[list(float)]): The bids or asks in the
                form of (price, volume).

        Returns:
            float: Prospective price of a market buy or sell.

        Raises:
            RuntimeError: If the orderbook is not deep enough.
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
            usd_value = super(TradingClient, self).convert_to_usd(
                self.target_amount)
            return usd_value / asset_volume

    def load_markets(self):
        """Load the markets of the exchange."""
        self.ccxt_exchange.load_markets()

    def set_conversion_needed(self, flag):
        """Indicates whether a conversion is needed for the quote currency.

        Args:
            flag (bool): True or False depending on whether conversion needed.
        """
        self.conversion_needed = flag
