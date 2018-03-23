import ccxt

from basefetcher import BaseFetcher


class RealTimeFetcher(BaseFetcher):
    """API data fetcher for real-time data."""

    def __init__(self, base, quote, exchange):
        """Constructor.

        Fetches real-time data from the specified exchange.

        Args:
            base (str): The base (first) token/currency of the exchange pair.
            quote (str): The quote (second) token/currency of the exchange pair.
            exchange (str): Desired exchange to query against.
        """
        super(RealTimeFetcher, self).__init__(base, quote, exchange)
        self.ccxt_exchange = getattr(ccxt, exchange.lower())()

    def fetch_last_price(self):
        """Fetches the last transacted price of the token pair.

        Returns:
            int: The last transacted price of the token pair.
        """
        pairsequence = (self.base, "/", self.quote)
        ticker = self.ccxt_exchange.fetch_ticker(''.join(pairsequence))
        return str(ticker['last'])