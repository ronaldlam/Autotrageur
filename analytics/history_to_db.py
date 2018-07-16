"""Historical prices to database.

Updates database with historical prices of a trading pair.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import logging

import MySQLdb
from warnings import filterwarnings
import yaml

from libs.trade.fetcher.history_fetcher import (HistoryFetcher,
    HistoryQueryParams)
from libs.fiat_symbols import FIAT_SYMBOLS
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


def row_add_info(row, base, quote, exchange):
    """Appends additional information to an existing row of historical data.

    Args:
        row (dict): A row of historical data, represented as a dict.
        base (str): The base currency.
        quote (str): The quote currency.
        exchange (str): The exchange associated with the retrieved data.
    """
    if row['volumefrom'] > 0:
        vwap = row['volumeto'] / row['volumefrom']
    else:
        vwap = 0
    row.update({
        'vwap': vwap,
        'base': base,
        'quote': quote,
        'exchange': exchange
    })


def fetch_history(fetcher):
    """Fetches token history.

    NOTE: For use with a multithreading executor.

    Args:
        fetcher (HistoryFetcher): The fetcher used to interface with and
            retrieve historical data.

    Returns:
        list[dict]: The historical data received from an API.
    """
    return fetcher.get_token_history(fetcher.interval)


def make_fetchers(cfg_filepaths):
    """Creates a list of HistoryFetchers.

    Args:
        cfg_filepaths (list[str]): A list of config filepaths containing the
            metadata required for fetching a trading pair's history.

    Raises:
        IncompatibleTimeIntervalError: Thrown if an invalid TimeInterval is
            given.

    Returns:
        list[HistoryFetcher]: A list of constructed HistoryFetchers for each
            config file provided.
    """
    hist_fetchers = []
    for cfg_file in cfg_filepaths:
        with open(cfg_file, 'r') as in_configfile:
            config = yaml.safe_load(in_configfile)

            # General config.
            basecurr = config['base']
            quotecurr = config['quote']
            exchange = config['exchange']
            interval = config['interval']
            limit = config['limit']

            if not TimeInterval.has_value(interval):
                raise IncompatibleTimeIntervalError("Time interval must be one"
                                                    " of: 'day', 'hour', "
                                                    "'minute'.")

            toTs = get_most_recent_rounded_timestamp(interval)
            logging.info("Calculated nearest current timestamp: " + str(toTs))

            history_params = HistoryQueryParams(
                basecurr, quotecurr, exchange, None, None, None, 1,
                limit, toTs)
            hist_fetchers.append(HistoryFetcher(history_params, interval))
    return hist_fetchers


def persist_to_db(db_name, db_user, db_password, hist_fetchers):
    """Connects to DB and inserts data.

    Given the given credentials, connects to a database, creates a table (if
    necessary), and inserts historical data.

    Args:
        db_name (str): Database name.
        db_user (str): Database user.
        db_password (str): Database password.
        hist_fetchers (list[HistoryFetcher]): A list of fetchers containing
            metadata, and used for fetching historical data through an API.
    """
    db = MySQLdb.connect(user=db_user, passwd=db_password, db=db_name)
    cursor = db.cursor()

    with ThreadPoolExecutor(max_workers=30) as executor:
        future_to_fetcher = {
            executor.submit(fetch_history, fetcher): fetcher for fetcher in hist_fetchers
        }
        for future in as_completed(future_to_fetcher):
            fetcher = future_to_fetcher[future]
            try:
                price_history = future.result()
            except Exception as exc:
                logging.info("{} fetching generated an exception: {}".format(
                    fetcher.exchange, exc))
            else:
                base = fetcher.base
                quote = fetcher.quote
                exchange = fetcher.exchange
                interval = fetcher.interval

                # Add the extra columns.
                for row in price_history:
                    row_add_info(row, base, quote, exchange)

                # Create table if needed and insert data.
                if logging.getLogger().getEffectiveLevel() < logging.INFO:
                    filterwarnings('ignore', category=MySQLdb.Warning)
                dec_prec = '(11, 2)' if quote.upper() in FIAT_SYMBOLS else '(18,9)'
                tablename = ''.join([exchange, base, quote, interval])
                cursor.execute("CREATE TABLE IF NOT EXISTS " + tablename +
                    "(time INT(11) UNSIGNED NOT NULL,\n"
                    "close DECIMAL" + dec_prec + " UNSIGNED NOT NULL,\n"
                    "high DECIMAL" + dec_prec + " UNSIGNED NOT NULL,\n"
                    "low DECIMAL" + dec_prec + " UNSIGNED NOT NULL,\n"
                    "open DECIMAL" + dec_prec + " UNSIGNED NOT NULL,\n"
                    "volumefrom DECIMAL(13, 4) UNSIGNED NOT NULL,\n"
                    "volumeto DECIMAL(13, 4) UNSIGNED NOT NULL,\n"
                    "vwap DECIMAL(13, 4) UNSIGNED NOT NULL,\n"
                    "base VARCHAR(10) NOT NULL,\n"
                    "quote VARCHAR(10) NOT NULL,\n"
                    "exchange VARCHAR(28) NOT NULL,\n"
                    "PRIMARY KEY (time));")
                cursor.executemany("INSERT IGNORE INTO "
                    + tablename
                    + "(time, close, high, low, open, volumefrom, volumeto, vwap, base,"
                    + " quote, exchange)\n"
                    + "VALUES (%(time)s, %(close)s, %(high)s, %(low)s, %(open)s,"
                    + " %(volumefrom)s, %(volumeto)s, %(vwap)s, %(base)s, %(quote)s,"
                    + " %(exchange)s)",
                    price_history)
                cursor.close()
                db.commit()
