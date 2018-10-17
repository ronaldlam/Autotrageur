"""Current forex rates to database.

Updates database with current spot prices of a trading pair.
"""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pprint import pformat
from time import time

import yaml

import libs.db.maria_db_handler as db_handler
from libs.constants.decimal_constants import ONE
from libs.forex.currency_converter import convert_currencies_primary


def _get_conversion(pair):
    """Fetches forex conversion for pair.

    NOTE: For use with a multithreading executor.

    Args:
        pair (tuple(str, str)): The forex pair to fetch data for.

    Returns:
        list[dict]: The historical data received from an API.
    """
    base, quote = pair
    return convert_currencies_primary(base, quote, ONE)


def get_pairs(config_file):
    """Retrieves list of pairs from the given file.

    Args:
        config_file (str): A config filepath containing the list of
            desired pairs.

    Returns:
        list[(str, str)]: A list of pairs to fetch data for.
    """
    with open(config_file, 'r') as in_configfile:
        config = yaml.safe_load(in_configfile)
        logging.info('Pairs: {}'.format(pformat(config['pairs'])))
        return [tuple(pair) for pair in config['pairs']]


def prepare_tables(currency_pairs):
    """Creates the tables for the data if they do not exist.

    Args:
        currency_pairs (list[(str, str)]): List of base/quote pairs.
    """
    for base, quote in currency_pairs:
        # Create table if needed.
        table_name = ''.join([base, quote, 'minute'])
        db_handler.execute_ddl(
            "CREATE TABLE IF NOT EXISTS " + table_name +
                "(time INT(11) UNSIGNED NOT NULL,\n"
                "price DECIMAL(18,9) UNSIGNED NOT NULL,\n"
                "base VARCHAR(10) NOT NULL,\n"
                "quote VARCHAR(10) NOT NULL,\n"
                "PRIMARY KEY (time))")
    logging.info('Tables prepared.')


def persist_to_db(currency_pairs):
    """Connects to DB and inserts data.

    Given the given credentials, connects to a database, creates a table (if
    necessary), and inserts current data.

    Args:
        currency_pairs (list[(str, str)]): A list of tuples containing
            base/quote pairs.
    """
    logging.info('Running persist_to_db...')
    with ThreadPoolExecutor(max_workers=30) as executor:
        future_to_pair = {
            executor.submit(_get_conversion, pair): pair for pair in currency_pairs
        }
        current_time = int(time())
        for future in as_completed(future_to_pair):
            pair = future_to_pair[future]
            try:
                price = future.result()
            except Exception as exc:
                logging.info("Fetching {} failed: {}".format(
                    pair, exc))
            else:
                base, quote = pair
                table_name = ''.join([base, quote, 'minute'])
                row = {
                    'time': current_time,
                    'price': price,
                    'base': base,
                    'quote': quote
                }

                insert_obj = db_handler.InsertRowObject(table_name, row, ('time',))
                db_handler.insert_row(insert_obj)
                logging.info('{}/{} fetch complete.'.format(base, quote))
    db_handler.commit_all()
    logging.info('Committed.')


def start_db(db_user, db_password, db_name):
    """Proxy to maria_db_handler.start_db.

    Args:
        db_user (str): The database user.
        db_password (str): The database password.
        db_name (str): The database name.
    """
    logging.info('DB started.')
    db_handler.start_db(db_user, db_password, db_name)
