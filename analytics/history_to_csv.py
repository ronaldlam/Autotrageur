"""Historical prices to csv.

Creates a csv file from historical prices of a trading pair.

Usage:
    history_to_csv.py CONFIGFILE
"""

import os
import sys
import inspect

# Add parent dir onto the sys.path.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from enum import Enum
import time

import libs.cryCompare.history as tokenhistory
from docopt import docopt
import yaml

import libs.csv.csvmaker as csvmaker

# Constants
MINUTES_TO_SECONDS = 60
HOURS_TO_SECONDS = MINUTES_TO_SECONDS * 60
DAYS_TO_SECONDS = HOURS_TO_SECONDS * 24
DAYS_IN_YEAR = 365
HOURS_IN_YEAR = DAYS_IN_YEAR * 24
CSV_COL_HEADERS = [
        'time',
        'close',
        'high',
        'low',
        'open',
        'volumefrom',
        'volumeto'
]

# CryptoCompare limitations
CC_MAX_ROWS = 2000


class TimeInterval(Enum):
    """An enum for time intervals

    Args:
        Enum (int): One of:
        - Minutes
        - Hours
        - Days
    """
    MINUTES = 'minutes'
    HOURS = 'hours'
    DAYS = 'days'

    @classmethod
    def has_value(cls, value):
        """Checks if a value is in the TimeInterval Enum.

        Args:
            value (str): A string value to check against the TimeInterval Enum.

        Returns:
            bool: True if value belongs in TimeInterval Enum. Else, false.
        """
        return any(value.lower() == item.value for item in cls)


class IncompatibleTimeIntervalError(Exception):
        """Raised when a value does not belong within the TimeInterval Enum."""
        pass


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


def get_most_recent_rounded_timestamp(interval):
    """Obtains the most recent, rounded timestamp.

    Args:
        interval (str): The time interval.  One of 'days', 'hours', 'minutes'.

    Returns:
        float: The most recent, rounded timestamp.
    """
    curr_time = time.time()
    if interval == TimeInterval.MINUTES.value:
        return curr_time - (curr_time % MINUTES_TO_SECONDS)
    elif interval == TimeInterval.HOURS.value:
        return curr_time - (curr_time % HOURS_TO_SECONDS)
    elif interval == TimeInterval.DAYS.value:
        return curr_time - (curr_time % DAYS_TO_SECONDS)


def get_token_history(history_params, interval):
    """Obtains the token's price history.

    Args:
        history_params (HistoryQueryParams): Object containing the necessary
            query parameters for acquiring the token's price history through
            API.
        interval (str): Time interval between each price point of the history.

    Returns:
        list[dict]: A list of rows containing historical price points of the
            token being fetched.
    """
    history_data_points = []
    limit = history_params.limit
    while limit > 0:
        if interval == TimeInterval.MINUTES.value:
            history_data_points[0:0] = tokenhistory.histoMinute(
                history_params.base, history_params.quote,
                history_params.exchange, history_params.extraParams,
                history_params.sign, history_params.tryConversion,
                history_params.aggregate, limit, history_params.toTs)
        elif interval == TimeInterval.HOURS.value:
            history_data_points[0:0] = tokenhistory.histoHour(
                history_params.base, history_params.quote,
                history_params.exchange,history_params.extraParams,
                history_params.sign, history_params.tryConversion,
                history_params.aggregate, limit, history_params.toTs)
        elif interval == TimeInterval.DAYS.value:
            history_data_points[0:0] = tokenhistory.histoDay(
                history_params.base, history_params.quote,
                history_params.exchange, history_params.extraParams,
                history_params.sign, history_params.tryConversion,
                history_params.aggregate, limit, history_params.toTs,
                history_params.allData)
        if history_data_points:
            history_params.toTs = history_data_points[0]['time']
            print(history_params.toTs)
        limit -= CC_MAX_ROWS
    return history_data_points


if __name__ == "__main__":
    arguments = docopt(__doc__, version="HistoryToCSV 0.1")

    with open(arguments['CONFIGFILE'], "r") as in_configfile:
        config = yaml.load(in_configfile)

    basecurr = config['base']
    quotecurr = config['quote']
    exchange = config['exchange']
    interval = config['interval']
    limit = config['limit']
    if config['filename'] is None:
        filename = ''.join([basecurr, quotecurr, exchange, interval,
            str(limit), '.csv'])
    if not TimeInterval.has_value(interval):
        raise IncompatibleTimeIntervalError("Time interval must be one of:"
        "'days', hours', 'minutes'.")
    if os.path.exists(filename):
        sys.exit(filename + "already exists.  Please use another name or move "
        "the file.")

    # Prompt user with the configuration specified.
    user_confirm = ''
    while user_confirm.lower() != 'y':
        user_confirm = input(' '.join([">> You want to produce", filename,
            "with base currency", basecurr, "quote currency", quotecurr,
            "from exchange", exchange, "time interval", interval, "limit",
            str(limit), "Y/N ?"]))

    print(arguments)
    toTs = get_most_recent_rounded_timestamp(interval)
    print("Calculated nearest current timestamp: " + str(toTs))

    history_params = HistoryQueryParams(
        basecurr, quotecurr, exchange, None, None, None, 1,
        limit, toTs)
    price_history = get_token_history(
        history_params, interval)

    # TODO: Consider batching up writes to avoid size limitations with large
    # datasets
    csvmaker.dict_write_to_csv(
        CSV_COL_HEADERS,
        filename,
        price_history)



