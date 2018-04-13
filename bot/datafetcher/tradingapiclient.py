import logging
import sys

import ccxt

from .baseapiclient import BaseAPIClient


class OrderbookException(Exception):
    """Exception for orderbook related errors."""
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
        self.ccxt_exchange = getattr(ccxt, exchange.lower())(exchange_config)
        self.slippage = slippage
        self.target_amount = target_amount
        self.conversion_needed = False

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
            asset_price (float): Target asset price for exchanges with
                no market buy support.

        Returns:
            dict[dict, int]: Dictionary of response, includes 'info'
            and 'id'. The 'info' includes all response contents and
            result['id'] == result['info']['id']
        """
        if self.ccxt_exchange.id == "gemini":
            assert asset_price is not None
            # Calculated volume of asset expected to be purchased.
            volume = self.target_amount / asset_price
            # Maximum price we are willing to pay.
            # TODO: Implement failsafes for unreasonable slippage.
            ratio = (100.0 + self.slippage) / 100.0
            limit_price = round(asset_price * ratio, 2)

            logging.info("Gemini market buy.")
            logging.info("Estimated asset price: %s" % asset_price)
            logging.info("Volume: %s" % volume)
            logging.info("Limit price: %s" % limit_price)

            result = self.ccxt_exchange.create_limit_buy_order(
                "%s/%s" % (self.base, self.quote),
                volume,
                limit_price,
                {"options": ["immediate-or-cancel"]})
        else:
            result = self.ccxt_exchange.create_market_buy_order(
                "%s/%s" % (self.base, self.quote),
                self.target_amount)

        return result

    def execute_market_sell(self, asset_price, asset_amount):
        """Execute a market sell order.

        Args:
            asset_price (float): Target asset price for exchanges with
                no market sell support.
            asset_amount (float): Target amount of the asset to be sold.

        Returns:
            dict[dict, int]: Dictionary of response, includes 'info'
            and 'id'. The 'info' includes all response contents and
            result['id'] == result['info']['id']
        """
        if self.ccxt_exchange.id == "gemini":
            # Minimum price we are willing to sell.
            ratio = (100.0 - self.slippage) / 100.0
            limit_price = round(asset_price * ratio, 2)

            logging.info("Gemini market sell.")
            logging.info("Estimated asset price: %s" % asset_price)
            logging.info("Volume: %s" % asset_amount)
            logging.info("Limit price: %s" % limit_price)

            result = self.ccxt_exchange.create_limit_sell_order(
                "%s/%s" % (self.base, self.quote),
                asset_amount,
                limit_price,
                {"options": ["immediate-or-cancel"]})
        else:
            result = self.ccxt_exchange.create_market_sell_order(
                "%s/%s" % (self.base, self.quote),
                self.target_amount)

        return result

    def fetch_maker_fees(self):
        """Retrieve maker fees for given exchange.

        This function assumes worst case fees. For example, Gemini has a
        volume adjusted fee schedule that will benefit high volume
        traders. This is not accessible through their API and only post-
        trade fees can be retrieved. Also, ccxt seems to have incomplete
        information for Gemini.

        Raises:
            NotImplementedError: If not accessible through ccxt.

        Returns:
            float: The maker fee, given as a ratio.
        """
        # TODO: Review when upgrading past ccxt 1.11.163.
        if self.ccxt_exchange.id == "gemini":
            return 0.0025  # Hardcoded to 0.25%, verified through docs.
        elif self.ccxt_exchange.fees["trading"]["maker"]:
            return self.ccxt_exchange.fees["trading"]["maker"]
        else:
            logging.error(
                "Maker fees should be verified for %s" % self.ccxt_exchange.id)
            raise NotImplementedError("Manually verify fees please.")

    def fetch_taker_fees(self):
        """Retrieve taker fees for given exchange.

        This function assumes worst case fees. High volume discounts are not
        counted. See fetch_maker_fees() for additional details.

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

    def set_conversion_needed(self, flag):
        """Indicates whether a conversion is needed for the quote currency.

        Args:
            flag (bool): True or False depending on whether conversion needed.
        """
        self.conversion_needed = flag
