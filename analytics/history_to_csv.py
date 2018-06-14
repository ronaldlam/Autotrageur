"""Historical prices to csv.

Creates a csv file from historical prices of a trading pair.

Usage:
    history_to_csv.py CONFIGFILE
"""

from enum import Enum
import os
import sys
import inspect
import time

# Add parent dir onto the sys.path.
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from docopt import docopt
import pandas as pd
import yaml

from libs.trade.fetcher.history_fetcher import (HistoryFetcher,
    HistoryQueryParams)
from libs.time_utils import TimeInterval, get_most_recent_rounded_timestamp

# Constants
CSV_COL_HEADERS = [
        'time',
        'close',
        'high',
        'low',
        'open',
        'volumefrom',
        'volumeto',
        'vwap',
        'base',
        'quote',
        'exchange'
]


class IncompatibleTimeIntervalError(Exception):
        """Raised when a value does not belong within the TimeInterval Enum."""
        pass


if __name__ == "__main__":
    arguments = docopt(__doc__, version="HistoryToCSV 0.1")

    with open(arguments['CONFIGFILE'], "r") as in_configfile:
        config = yaml.load(in_configfile)

    basecurr = config['base']
    quotecurr = config['quote']
    exchange = config['exchange']
    interval = config['interval']
    limit = config['limit']
    filename = config['filename']
    if config['filename'] is None:
        filename = ''.join([basecurr, quotecurr, exchange, interval,
                            str(limit), '.csv'])
    if not TimeInterval.has_value(interval):
        raise IncompatibleTimeIntervalError("Time interval must be one of:"
                                            "'day', 'hour', 'minute'.")
    if os.path.exists(filename):
        sys.exit(filename + " already exists.  Please use another name or move "
                 "the file.")

    # Prompt user with the configuration specified.
    user_confirm = ''
    while user_confirm.lower() != 'y':
        user_confirm = input(' '.join([">> You want to produce", filename,
                                       "with base currency", basecurr,
                                       "quote currency", quotecurr,
                                       "from exchange", exchange,
                                       "time interval", interval, "limit",
                                       str(limit), "Y/N ?"]))

    toTs = get_most_recent_rounded_timestamp(interval)
    print("Calculated nearest current timestamp: " + str(toTs))

    history_params = HistoryQueryParams(
        basecurr, quotecurr, exchange, None, None, None, 1,
        limit, toTs)
    history_fetcher = HistoryFetcher(history_params)
    price_history = history_fetcher.get_token_history(interval)

    # Add the additional columns for the csv, through pandas.
    pricedf = pd.DataFrame(price_history, columns=CSV_COL_HEADERS)
    pricedf['vwap'] = pricedf['volumeto'] / pricedf['volumefrom']
    pricedf['base'] = basecurr
    pricedf['quote'] = quotecurr
    pricedf['exchange'] = exchange

    # TODO: Consider batching up writes to avoid memory limitations with large
    # datasets
    pricedf.to_csv(path_or_buf=filename, index=False)
