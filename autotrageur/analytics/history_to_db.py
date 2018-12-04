"""Historical prices to database.

Updates database with historical prices of a trading pair.
"""
import logging
import pprint
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor, as_completed, wait
from warnings import filterwarnings

import MySQLdb
import yaml

import fp_libs.db.maria_db_handler as db_handler
from fp_libs.email_client.simple_email_client import send_all_emails
from fp_libs.fiat_symbols import FIAT_SYMBOLS
from fp_libs.logging.logging_utils import fancy_log
from fp_libs.time_utils import TimeInterval, get_most_recent_rounded_timestamp
from fp_libs.trade.fetcher.cc_history_fetcher import CCHistoryFetcher
from fp_libs.trade.fetcher.cw_history_fetcher import CWHistoryFetcher
from fp_libs.trade.fetcher.history_fetcher import HistoryQueryParams


class IncompatibleTimeIntervalError(Exception):
        """Raised when a value does not belong within the TimeInterval Enum."""
        pass


class HistoryTableMetadata(namedtuple('HistoryTableMetadata', [
    'base', 'quote', 'exchange', 'interval', 'tablename'])):
    """Contains metadata, descriptive info about the historical table to be
    created.

    Args:
        base (str): The base asset for the table.
        quote (str): The quote asset for the table.
        exchange (str): The exchange for the table.
        interval (str): The time interval for the table, such as 'minute'.
        tablename (str): The table's name.
    """
    __slots__ = ()


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


def make_fetchers(cfg_filepaths, fetcher_type):
    """Creates a list of HistoryFetchers.

    Args:
        cfg_filepaths (list[str]): A list of config filepaths containing the
            metadata required for fetching a trading pair's history.
        fetcher_type (str): One of ['cc', 'cw'], for CryptoCompare or
            Cryptowatch datasources.

    Raises:
        IncompatibleTimeIntervalError: Thrown if an invalid TimeInterval is
            given.
        NotImplementedError: If fetcher_type is not supported.

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

            if fetcher_type == 'cc':
                fetcher = CCHistoryFetcher(history_params, interval)
            elif fetcher_type == 'cw':
                fetcher = CWHistoryFetcher(history_params, interval)
            else:
                raise NotImplementedError(
                    'Only cc or cw fetcher types supported.')

            hist_fetchers.append(fetcher)
    return hist_fetchers


def prepare_tables(table_metadata_list):
    """Creates the tables for historical data if they don't exist.

    Args:
        table_metadata_list (list[HistoryTableMetadata]): List of
            HistoryTableMetadata for determining what tables to create.
    """
    for table_metadata in table_metadata_list:
        # Create table if needed.
        dec_prec = '(11,2)' if table_metadata.quote.upper() in FIAT_SYMBOLS else '(18,9)'
        db_handler.execute_ddl(
            "CREATE TABLE IF NOT EXISTS " + table_metadata.tablename +
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
    logging.info('Tables prepared.')


def persist_to_db(hist_fetchers, email_cfg_path):
    """Inserts minute data.

    Creates a table (if necessary), and inserts historical data.  Requires
    an open DB connection.

    Args:
        hist_fetchers (list[HistoryFetcher]): A list of fetchers containing
            metadata, and used for fetching historical data through an API.
        email_cfg_path (str): Path to e-mail configuration for sending emails.
    """
    cached_exceptions = []
    cached_exceptions_exchange_names = []
    cached_successful_inserts_metadata = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_fetcher = {
            executor.submit(fetch_history, fetcher): fetcher for fetcher in hist_fetchers
        }
        for future in as_completed(future_to_fetcher):
            fetcher = future_to_fetcher[future]
            try:
                price_history = future.result()
            except Exception as exc:
                cached_exceptions_exchange_names.append(fetcher.exchange)
                cached_exceptions.append(exc)
            else:
                if logging.getLogger().getEffectiveLevel() < logging.INFO:
                    filterwarnings('ignore', category=MySQLdb.Warning)  # pylint: disable=E1101

                base = fetcher.base
                quote = fetcher.quote
                exchange = fetcher.exchange
                interval = fetcher.interval
                tablename = ''.join([exchange, base, quote, interval])

                # Add the extra columns.
                for row in price_history:
                    fetcher.adjust_row_info(row, base, quote, exchange)

                cursor = db_handler.db.cursor()
                cursor.executemany("INSERT IGNORE INTO "
                    + tablename
                    + "(time, close, high, low, open, volumefrom, volumeto, vwap, base,"
                    + " quote, exchange)\n"
                    + "VALUES (%(time)s, %(close)s, %(high)s, %(low)s, %(open)s,"
                    + " %(volumefrom)s, %(volumeto)s, %(vwap)s, %(base)s, %(quote)s,"
                    + " %(exchange)s) "
                    + "ON DUPLICATE KEY UPDATE time=time",
                    price_history)
                db_handler.db.commit()

                # Add successful row insertion metadata.
                if not cached_successful_inserts_metadata.get(exchange):
                    cached_successful_inserts_metadata[exchange] = [{
                        'base': base,
                        'quote': quote,
                        'rows_updated': cursor.rowcount
                    }]
                else:
                    cached_successful_inserts_metadata[exchange].append({
                        'base': base,
                        'quote': quote,
                        'rows_updated': cursor.rowcount
                    })

                # Cleanup.
                cursor.close()

        wait(future_to_fetcher)
        fancy_log("SUCCESSFUL INSERTS")
        logging.info(pprint.pformat(cached_successful_inserts_metadata))

        email_msg_entries = []
        fancy_log("Exceptions during fetching")
        for exchange_name, exc in zip(cached_exceptions_exchange_names, cached_exceptions):
            exception_msg = "{} fetching generated an exception: {}".format(
                exchange_name, exc)
            logging.info(exception_msg)
            email_msg_entries.append(exception_msg + '\n')

        # Send email to admin if any errors during fetching.
        if email_msg_entries:
            send_all_emails(
                email_cfg_path,
                "Minute Data Fetching Error Report",
                ''.join(email_msg_entries))
