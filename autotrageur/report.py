"""Generate stats for an Autotrageur run.

Prints a summary of the performance of the specified run.

Usage:
    report.py KEY_FILE CONFIG_ID DB_CONFIG [START_BALANCES] [--pi_mode]

Options:
    --pi_mode           Whether this is to be used with the raspberry pi or on a full desktop.

Description:
    KEY_FILE            The encrypted key file containing relevant api keys.
    CONFIG_ID           The autotrageur config id.
    DB_CONFIG           The config file for the database.
    START_BALANCES      The config file containing start balance info.
"""
import getpass
import logging

import yaml
from docopt import docopt

from autotrageur.version import VERSION
from fp_libs.db.maria_db_handler import execute_parametrized_query, start_db
from fp_libs.forex.currency_converter import convert_currencies
from fp_libs.trade.fetcher.ccxt_fetcher import CCXTFetcher
from fp_libs.utilities import (load_exchange, load_keyfile, num_to_decimal,
                               split_symbol)


def main():
    """Installed entry point."""
    arguments = docopt(__doc__, version=VERSION)
    logging.basicConfig(format="%(asctime)s %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    logging.getLogger().setLevel(logging.INFO)

    with open(arguments['DB_CONFIG'], 'r') as db_info:
        db_info = yaml.safe_load(db_info)
        db_user = db_info['db_user']
        db_name = db_info['db_name']

    db_password = getpass.getpass('DB password:')
    start_db(db_user, db_password, db_name)

    if arguments['START_BALANCES']:
        with open(arguments['START_BALANCES'], 'r') as balance_info:
            balance_info = yaml.safe_load(balance_info)
            start_e1_base = num_to_decimal(balance_info['e1_base'])
            start_e1_quote = num_to_decimal(balance_info['e1_quote'])
            start_e2_base = num_to_decimal(balance_info['e2_base'])
            start_e2_quote = num_to_decimal(balance_info['e2_quote'])

    # As is, the BIT MariaDB type will return b'\x00' or b'\x01'. We use
    # INTEGER since it's better behaved as a python int.
    market_info = execute_parametrized_query(
        'SELECT exchange1, exchange2, exchange1_pair, exchange2_pair, CAST(use_test_api AS INTEGER) '
        'FROM fcf_autotrageur_config '
        'WHERE id=%s '
        'ORDER BY start_timestamp '
        'LIMIT 1',
        (arguments['CONFIG_ID'],)
    )
    e1_name, e2_name, e1_pair, e2_pair, use_test_api = market_info[0]

    exchange_key_map = load_keyfile(
        arguments['KEY_FILE'], arguments['--pi_mode'])
    e1 = load_exchange(e1_name, exchange_key_map, use_test_api)
    e2 = load_exchange(e2_name, exchange_key_map, use_test_api)

    e1_fetcher = CCXTFetcher(e1)
    e2_fetcher = CCXTFetcher(e2)
    e1_base, e1_quote = split_symbol(e1_pair)
    e2_base, e2_quote = split_symbol(e2_pair)
    current_e1_base, current_e1_quote = e1_fetcher.fetch_free_balances(
        e1_base, e1_quote)
    current_e2_base, current_e2_quote = e2_fetcher.fetch_free_balances(
        e2_base, e2_quote)

    logging.info('Start Balances:')
    logging.info('{:<10} {}'.format(e1_base + ':', start_e1_base))
    logging.info('{:<10} {}'.format(e1_quote + ':', start_e1_quote))
    logging.info('{:<10} {}'.format(e2_base + ':', start_e2_base))
    logging.info('{:<10} {}'.format(e2_quote + ':', start_e2_quote))
    logging.info('Current Balances:')
    logging.info('{:<10} {}'.format(e1_base + ':', current_e1_base))
    logging.info('{:<10} {}'.format(e1_quote + ':', current_e1_quote))
    logging.info('{:<10} {}'.format(e2_base + ':', current_e2_base))
    logging.info('{:<10} {}'.format(e2_quote + ':', current_e2_quote))
    logging.info('Balance Differences:')
    logging.info('{:<10} {}'.format(e1_base + ':', current_e1_base - start_e1_base))
    logging.info('{:<10} {}'.format(e1_quote + ':', current_e1_quote - start_e1_quote))
    logging.info('{:<10} {}'.format(e2_base + ':', current_e2_base - start_e2_base))
    logging.info('{:<10} {}'.format(e2_quote + ':', current_e2_quote - start_e2_quote))

    usd_start_e1_quote = convert_currencies(e1_quote, 'USD', start_e1_quote)
    usd_start_e2_quote = convert_currencies(e2_quote, 'USD', start_e2_quote)
    usd_current_e1_quote = convert_currencies(e1_quote, 'USD', current_e1_quote)
    usd_current_e2_quote = convert_currencies(e2_quote, 'USD', current_e2_quote)

    usd_e1_quote_diff = usd_current_e1_quote - usd_start_e1_quote
    usd_e2_quote_diff = usd_current_e2_quote - usd_start_e2_quote

    logging.info('Profitability, current forex:')
    logging.info('{:<10} {}'.format('USD:', usd_e1_quote_diff + usd_e2_quote_diff))


if __name__ == "__main__":
    main()
