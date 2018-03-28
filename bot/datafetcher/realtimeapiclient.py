import ccxt

from .baseapiclient import BaseAPIClient


class RealTimeAPIClient(BaseAPIClient):
    """API Client for real-time data."""

    def __init__(self, base, quote, exchange, exchange_config=None):
        """Constructor.

        Fetches real-time data from the specified exchange.

        Args:
            base (str): The base (first) token/currency of the exchange pair.
            quote (str): The quote (second) token/currency of the exchange pair.
            exchange (str): Desired exchange to query against.
            exchange_config (dict): The exchange's configuration in accordance
                with the ccxt library for instantiating an exchange.
                Ex.
                {
                    "apiKey": [SOME_API_KEY]
                    "secret": [SOME_API_SECRET]
                    "verbose": False,
                }

        """
        super(RealTimeAPIClient, self).__init__(base, quote, exchange)
        self.ccxt_exchange = getattr(ccxt, exchange.lower())(exchange_config)
        self.conversion_needed = False

    def execute_market_order(self):
        """Executes a market buy or sell order"""
        pass

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
        return self.ccxt_exchange.fetch_order_book(self.base + "/" + self.quote)


    def get_market_price_from_orderbook(self, bids_or_asks, target_amount):
        """Get market buy or sell price

        Return potential market buy or sell price given bids or asks and
        amount to be sold. Input of bids will retrieve market sell price;
        input of asks will retrieve market buy price.

        Args:
            bids_or_asks (list[(int, int)]): The bids or asks in the form of
                (price, volume).
            target_amount (int): The amount to prospectively market buy/sell.

        Returns:
            float: Prospective price of a market buy or sell.

        Raises:
            RuntimeError: If the orderbook is not deep enough.
        """

        index = 0
        asset_volume = 0.0
        original_amount = target_amount

        # Subtract from amount until enough of the order book is eaten up by
        # the trade.
        while target_amount > 0.0 and index < len(bids_or_asks):
            target_amount -= bids_or_asks[index][0] * bids_or_asks[index][1]
            asset_volume += bids_or_asks[index][1]
            index += 1

        if index == len(bids_or_asks) and target_amount > 0.0:
            # TODO: May not be a fatal error depending on whether we want the
            # bot to keep trying.
            raise RuntimeError("Order book not deep enough for trade.")

        # Add the zero or negative excess amount to trim off the overshoot
        asset_volume += target_amount / bids_or_asks[index - 1][0]

        if not self.conversion_needed:
            return original_amount/asset_volume
        else:
            return super(RealTimeAPIClient, self).convert_to_usd(original_amount)/asset_volume

    def set_conversion_needed(self, bFlag):
        """Indicates whether a conversion is needed for the quote currency.

        Args:
            bFlag (bool): True or False depending on whether conversion needed.
        """
        self.conversion_needed = bFlag