"""Historical prices to database.

Updates database with historical prices of a trading pair.

Usage:
    history_to_db.py CONFIGFILE
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
import MySQLdb
import pandas as pd
import yaml

from libs.trade.fetcher.history_fetcher import (HistoryFetcher,
    HistoryQueryParams, TimeInterval)

# Constants
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = SECONDS_PER_MINUTE * 60
SECONDS_PER_DAY = SECONDS_PER_HOUR * 24
DAY_PER_YEAR = 365
HOUR_IN_YEAR = DAY_PER_YEAR * 24
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

def get_most_recent_rounded_timestamp(interval):
        """Obtains the most recent, rounded timestamp.

        Args:
            interval (str): The time interval.  One of 'day', 'hour', 'minute'.

        Returns:
            float: The most recent, rounded timestamp.
        """
        curr_time = time.time()
        if interval == TimeInterval.MINUTE.value:
            return curr_time - (curr_time % SECONDS_PER_MINUTE)
        elif interval == TimeInterval.HOUR.value:
            return curr_time - (curr_time % SECONDS_PER_HOUR)
        elif interval == TimeInterval.DAY.value:
            return curr_time - (curr_time % SECONDS_PER_DAY)

if __name__ == "__main__":
    arguments = docopt(__doc__, version="HistoryToDB 0.1")

    with open(arguments['CONFIGFILE'], "r") as in_configfile:
        config = yaml.load(in_configfile)

    # General config.
    basecurr = config['base']
    quotecurr = config['quote']
    exchange = config['exchange']
    interval = config['interval']
    limit = config['limit']

    # DB config.
    db_user = config['db_user']
    db_password = config['db_password']
    db_name = config['db_name']
    if not TimeInterval.has_value(interval):
        raise IncompatibleTimeIntervalError("Time interval must be one of:"
                                            "'day', 'hour', 'minute'.")

    # Prompt user with the configuration specified.
    user_confirm = ''
    while user_confirm.lower() != 'y':
        user_confirm = input(' '.join([">> Insert to database: ", db_name,
                                       "\nwith base currency: ", basecurr,
                                       "\nquote currency: ", quotecurr,
                                       "\nfrom exchange: ", exchange,
                                       "\ntime interval: ", interval,
                                       "\nlimit: ", str(limit), "\nY/N ?"]))

    toTs = get_most_recent_rounded_timestamp(interval)
    print("Calculated nearest current timestamp: " + str(toTs))

    history_params = HistoryQueryParams(
        basecurr, quotecurr, exchange, None, None, None, 1,
        limit, toTs)
    history_fetcher = HistoryFetcher(history_params)
    price_history = history_fetcher.get_token_history(interval)

    # Add the extra columns.
    for row in price_history:
        if row['volumefrom'] > 0:
            vwap = row['volumeto'] / row['volumefrom']
        else:
            vwap = 0
        row.update({
            'vwap': vwap,
            'base': basecurr,
            'quote': quotecurr,
            'exchange': exchange
        })

    # Connect to DB, create table if needed and insert data.
    db=MySQLdb.connect(user=db_user, passwd=db_password, db=db_name)
    cursor = db.cursor()

    tablename = ''.join([exchange, basecurr, quotecurr, interval])
    cursor.execute("CREATE TABLE IF NOT EXISTS " + tablename +
        "(time INT(11) UNSIGNED NOT NULL,\n"
        "close DECIMAL(11, 2) UNSIGNED NOT NULL,\n"
        "high DECIMAL(11, 2) UNSIGNED NOT NULL,\n"
        "low DECIMAL(11, 2) UNSIGNED NOT NULL,\n"
        "open DECIMAL(11, 2) UNSIGNED NOT NULL,\n"
        "volumefrom DECIMAL(13, 4) UNSIGNED NOT NULL,\n"
        "volumeto DECIMAL(13, 4) UNSIGNED NOT NULL,\n"
        "vwap DECIMAL(13, 4) UNSIGNED NOT NULL,\n"
        "base VARCHAR(10) NOT NULL,\n"
        "quote VARCHAR(10) NOT NULL,\n"
        "exchange VARCHAR(28) NOT NULL,\n"
        "PRIMARY KEY (time));")
    cursor.executemany("INSERT IGNORE INTO " + tablename + "(time, close, high, low, open, volumefrom, volumeto, vwap, base, quote, exchange)\n"
        "VALUES (%(time)s, %(close)s, %(high)s, %(low)s, %(open)s, %(volumefrom)s, %(volumeto)s, %(vwap)s, %(base)s, %(quote)s, %(exchange)s)",
        price_history)
    db.commit()
    # import sqlalchemy
    # engine = sqlalchemy.create_engine('mysql://root:r and d@localhost', echo=True)
    # engine.execute('CREATE DATABASE IF NOT EXISTS ' + interval)
    # engine.execute('USE ' + interval)
    # pricedf.to_sql(con=engine, name=exchange + basecurr + quotecurr + interval, index=False, if_exists='append')