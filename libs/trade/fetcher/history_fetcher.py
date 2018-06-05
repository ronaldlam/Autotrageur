import logging

from libs.time_utils import TimeInterval
import thirdparty.cryCompare.history as tokenhistory

LOGGER = logging.getLogger()

# CryptoCompare limitations
CC_MAX_ROWS = 2000


class HistoryFetcher():
    """Fetcher for historical data."""

    def __init__(self, history_query_params):
        """Constructor.

        Args:
            history_query_params (HistoryQueryParams): Object containing the
                query parameters for obtaining historical prices from
                CryptoCompare API.
        """
        self.base = history_query_params.base
        self.quote = history_query_params.quote
        self.exchange = history_query_params.exchange
        self.extraParams = history_query_params.extraParams
        self.sign = history_query_params.sign
        self.tryConversion = history_query_params.tryConversion
        self.aggregate = history_query_params.aggregate
        self.limit = history_query_params.limit
        self.toTs = history_query_params.toTs
        self.allData = history_query_params.allData

    def get_token_history(self, interval):
        """Obtains the token's price history.

        Args:
            interval (str): Time interval between each price point of the history.

        Returns:
            list[dict]: A list of rows containing historical price points of the
                token being fetched.
        """
        history_data_points = []
        limit = self.limit
        while limit > 0:
            if interval == TimeInterval.MINUTE.value:
                history_data_points[0:0] = tokenhistory.histoMinute(
                    self.base, self.quote,
                    self.exchange, self.extraParams,
                    self.sign, self.tryConversion,
                    self.aggregate, limit, self.toTs)
            elif interval == TimeInterval.HOUR.value:
                history_data_points[0:0] = tokenhistory.histoHour(
                    self.base, self.quote,
                    self.exchange, self.extraParams,
                    self.sign, self.tryConversion,
                    self.aggregate, limit, self.toTs)
            elif interval == TimeInterval.DAY.value:
                history_data_points[0:0] = tokenhistory.histoDay(
                    self.base, self.quote,
                    self.exchange, self.extraParams,
                    self.sign, self.tryConversion,
                    self.aggregate, limit, self.toTs,
                    self.allData)
            if history_data_points:
                self.toTs = history_data_points[0]['time']
                print(self.toTs)
            limit -= CC_MAX_ROWS
        return history_data_points


class HistoryQueryParams:
    """Encapsulates query parameters necessary for token history.

    See: https://min-api.cryptocompare.com/
    """

    def __init__(self, base, quote, exchange=None, extraParams=None,
                 sign=False, tryConversion=True, aggregate=None, limit=None,
                 toTs=None, allData=False):
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
                (for daily it's day, for hourly it's hour and for minute
                it's minute). Defaults to None.
            limit (int, optional): Number of data points to return.  Max is
                2000.  Defaults to None.
            toTs (int, optional): Last unix timestamp to return data for.
                Defaults to None, the present timestamp.
            allData (bool, optional): Returns all data (only available on
                histo day).  Defaults to False.
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