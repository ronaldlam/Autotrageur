import logging

from basefetcher import BaseFetcher

LOGGER = logging.getLogger()


class HistoryFetcher(BaseFetcher):
    """API data fetcher for historical data."""

    def __init__(self, history_query_params):
        """Constructor.

        Args:
            history_query_params (HistoryQueryParams): Object containing the
                query parameters for obtaining historical prices from an API.
        """
        # TODO: Create an exception to raise and re-instantiate this.
        if not isinstance(history_query_params, HistoryQueryParams):
            LOGGER.warning("Instantiating a HistoryFetcher without \
                            HistoryQueryParams as a parameter")
        super(HistoryFetcher, self).__init__(
            history_query_params.base, history_query_params.quote,
            history_query_params.exchange)
        self.extraParams = history_query_params.extraParams
        self.sign = history_query_params.sign
        self.tryConversion = history_query_params.tryConversion
        self.aggregate = history_query_params.aggregate
        self.limit = history_query_params.limit
        self.toTs = history_query_params.toTs
        self.allData = history_query_params.allData


class HistoryQueryParams:
    """Encapsulates query parameters necessary for token history.

    See: https://min-api.cryptocompare.com/
    """

    def __init__(self, base, quote, exchange=None, extraParams=None,
                 sign=False, tryConversion=True, aggregate=None, limit=None,
                 toTs=None, allData=None):
        """Constructor.

        Args:
            base (str): The base (first) token/currency of the exchange pair.
            quote (str): The quote (second) token/currency of the exchange pair.
            exchange (str, optional): Desired exchange to query against.
                Defaults to CryptoCompare's CCCAGG if None given.
            extraParams (str, optional): Extra parameters.  For example, your
                app name. Defaults to None.
            sign (bool, optional): If set to True, the server will sign the
                requests, this is useful for
                usage in smart contracts.  Defaults to False.
            tryConversion (bool, optional): If set to false, it will try to get
                only direct trading values.  Defaults to True.
            aggregate (int, optional): Time period to aggregate the data over
                (for daily it's days, for hourly it's hours and for minute
                histo it's minutes). Defaults to None.
            limit (int, optional): Number of data points to return.  Max is
                2000.  Defaults to None.
            toTs (int, optional): Last unix timestamp to return data for.
                Defaults to None, the present timestamp.
            allData (bool, optional): Returns all data (only available on
                histo day).  Defaults to None.
        """
        self.base = base
        self.quote = quote
        self.exchange = exchange
        self.extraParams = extraParams
        self.sign = sign
        self.tryConversion = tryConversion
        self.aggregate = aggregate
        self.limit = limit
        self.toTs = toTs
        self.allData = allData