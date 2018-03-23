class BaseFetcher:
    """Base class for an API data fetcher."""

    def __init__(self, base, quote, exchange):
        """Constructor.

        Args:
            base (str): The base (first) token/currency of the exchange pair.
            quote (str): The quote (second) token/currency of the exchange pair.
            exchange (str): Desired exchange to query against.
        """
        self.base = base
        self.quote = quote
        self.exchange = exchange