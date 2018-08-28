import logging

import ccxt

from libs.utilities import num_to_decimal
from libs.utils.ccxt_utils import wrap_ccxt_retry


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
            Decimal: The maker fee, given as a ratio.
        """
        if self.exchange.fees["trading"]["maker"]:
            return num_to_decimal(self.exchange.fees["trading"]["maker"])
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
            Decimal: The taker fee, given as a ratio.
        """
        if self.exchange.fees["trading"]["taker"]:
            return num_to_decimal(self.exchange.fees["trading"]["taker"])
        else:
            logging.error(
                "Taker fees should be verified for %s" % self.exchange.id)
            raise NotImplementedError("Manually verify fees please.")

    def fetch_free_balances(self, base, quote):
        """Fetch balance of the base and quote assets in the account.

        Args:
            base (string): The base asset ticker.
            quote (string): The quote asset ticker.

        Returns:
            (Decimal, Decimal): The balances of the base and quote asset.
        """
        balance = wrap_ccxt_retry([self.exchange.fetch_balance])[0]
        return (num_to_decimal(balance[base]['free']),
                num_to_decimal(balance[quote]['free']))

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

        NOTE: Do not wrap this in `wrap_ccxt_retry` as we will likely need to
        retry multiple orderbook calls.

        Args:
            base (str): The base currency of the token pair.
            quote (str): The quote currency of the token pair.

        Returns:
            dict: The full orderbook.
        """
        return self.exchange.fetch_order_book(base + "/" + quote) #params={'limit_bids':200, 'limit_asks':200})

    def load_markets(self):
        """Load the markets of the exchange.

        Allows manual calling of `load_markets` from either a ccxt Exchange
        object or a `ccxt_extensions` ext_ Exchange object.

        Refer https://github.com/ccxt/ccxt/wiki/Manual in the Loading Markets
        section for details.

        Returns:
            dict: Information about the `markets` which have been loaded into
                memory.
        """
        return wrap_ccxt_retry([self.exchange.load_markets])[0]
