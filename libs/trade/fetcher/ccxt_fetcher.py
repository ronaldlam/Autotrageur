import logging
import ccxt


class CCXTFetcher():
    """Fetcher for CCXT library."""

    def __init__(self, exchange):
        """Constructor.

        Args:
            exchange (ccxt_exchange): A CCXT exchange object.
        """
        if not isinstance(exchange, ccxt.Exchange):
            raise TypeError("CCXTFetcher must initialize with a ccxt exchange"
                " object")
        self.exchange = exchange

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
        if self.exchange.fees["trading"]["maker"]:
            return self.exchange.fees["trading"]["maker"]
        else:
            logging.error(
                "Maker fees should be verified for %s" % self.exchange.id)
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
        if self.exchange.fees["trading"]["taker"]:
            return self.exchange.fees["trading"]["taker"]
        else:
            logging.error(
                "Taker fees should be verified for %s" % self.exchange.id)
            raise NotImplementedError("Manually verify fees please.")

    def fetch_free_balance(self, asset):
        """Fetch balance of the given asset in the account.

        Args:
            asset (string): The balance of the given asset

        Returns:
            float: The balances of the given asset.
        """
        balance = self.exchange.fetch_balance()
        return balance[asset]["free"]

    def fetch_last_price(self, base, quote):
        """Fetches the last transacted price of the token pair.

        Args:
            base (str): The base currency of the token pair.
            quote (str): The quote currency of the token pair.

        Returns:
            int: The last transacted price of the token pair.
        """
        pairsequence = (base, "/", quote)
        ticker = self.exchange.fetch_ticker(''.join(pairsequence))
        return str(ticker['last'])

    def get_full_orderbook(self, base, quote):
        """Gets the full orderbook (bids and asks) from the exchange.

        Return value example:
        {
            'bids': [
                [ price, amount ], // [ float, float ]
                [ price, amount ],
                ...
            ],
            'asks': [
                [ price, amount ],
                [ price, amount ],
                ...
            ],
            'timestamp': 1499280391811, // Unix Timestamp in milliseconds (seconds * 1000)
            'datetime': '2017-07-05T18:47:14.692Z', // ISO8601 datetime string with milliseconds
        }

        Args:
            base (str): The base currency of the token pair.
            quote (str): The quote currency of the token pair.

        Returns:
            dict: The full orderbook.
        """
        return self.exchange.fetch_order_book(base + "/" + quote)
