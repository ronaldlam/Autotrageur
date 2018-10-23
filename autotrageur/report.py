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
import time

import yaml
from docopt import docopt

from autotrageur.version import VERSION
from fp_libs.ccxt_extensions.exchange_loader import load_exchange
from fp_libs.constants.decimal_constants import HUNDRED, ONE
from fp_libs.db.maria_db_handler import execute_parametrized_query, start_db
from fp_libs.forex.currency_converter import convert_currencies
from fp_libs.trade.fetcher.ccxt_fetcher import CCXTFetcher
from fp_libs.utilities import load_keyfile, num_to_decimal, split_symbol


# Logging constants
START_END_FORMAT = "{} {:^30} {}"
STARS = "*"*20


def capitalize(string):
    """Capitalize the given string

    Args:
        string (str): The string input.
    """
    return string[0].upper() + string[1:]


def fancy_log(title):
    """Log an empty line and title surrounded by stars."""
    logging.info('')
    logging.info(START_END_FORMAT.format(STARS, title, STARS))


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
        (arguments['CONFIG_ID'],))
    e1_name, e2_name, e1_pair, e2_pair, use_test_api = market_info[0]
    e1_base, e1_quote = split_symbol(e1_pair)
    e2_base, e2_quote = split_symbol(e2_pair)

    start_timestamp = execute_parametrized_query(
        'SELECT start_timestamp '
        'FROM fcf_autotrageur_config '
        'WHERE id=%s '
        'ORDER BY start_timestamp '
        'LIMIT 1',
        (arguments['CONFIG_ID'],))[0][0]
    trade_count = execute_parametrized_query(
        'SELECT COUNT(*) '
        'FROM trades '
        'WHERE autotrageur_config_id=%s',
        (arguments['CONFIG_ID'],))[0][0]
    e1_base_volume, e1_quote_volume = execute_parametrized_query(
        'SELECT SUM(pre_fee_base), SUM(post_fee_quote) '
        'FROM trades '
        'WHERE autotrageur_config_id=%s AND exchange=%s',
        (arguments['CONFIG_ID'], e1_name))[0]
    e2_base_volume, e2_quote_volume = execute_parametrized_query(
        'SELECT SUM(pre_fee_base), SUM(post_fee_quote) '
        'FROM trades '
        'WHERE autotrageur_config_id=%s AND exchange=%s',
        (arguments['CONFIG_ID'], e2_name))[0]

    if e1_quote != 'USD':
        e1_start_rate = execute_parametrized_query(
            'SELECT f.rate '
            'FROM fcf_autotrageur_config c, forex_rate f '
            'WHERE f.local_timestamp >= c.start_timestamp AND c.id=%s AND f.quote=%s '
            'ORDER BY f.local_timestamp '
            'LIMIT 1',
            (arguments['CONFIG_ID'], e1_quote))[0][0]
    if e2_quote != 'USD':
        e2_start_rate = execute_parametrized_query(
            'SELECT f.rate '
            'FROM fcf_autotrageur_config c, forex_rate f '
            'WHERE f.local_timestamp >= c.start_timestamp AND c.id=%s AND f.quote=%s '
            'ORDER BY f.local_timestamp '
            'LIMIT 1',
            (arguments['CONFIG_ID'], e2_quote))[0][0]

    exchange_key_map = load_keyfile(
        arguments['KEY_FILE'], arguments['--pi_mode'])
    e1 = load_exchange(e1_name, exchange_key_map, use_test_api)
    e2 = load_exchange(e2_name, exchange_key_map, use_test_api)

    e1_fetcher = CCXTFetcher(e1)
    e2_fetcher = CCXTFetcher(e2)
    current_e1_base, current_e1_quote = e1_fetcher.fetch_free_balances(
        e1_base, e1_quote)
    current_e2_base, current_e2_quote = e2_fetcher.fetch_free_balances(
        e2_base, e2_quote)

    usd_start_e1_quote = convert_currencies(e1_quote, 'USD', start_e1_quote)
    usd_start_e2_quote = convert_currencies(e2_quote, 'USD', start_e2_quote)
    usd_current_e1_quote = convert_currencies(e1_quote, 'USD', current_e1_quote)
    usd_current_e2_quote = convert_currencies(e2_quote, 'USD', current_e2_quote)

    usd_start_sum = usd_start_e1_quote + usd_start_e2_quote
    usd_current_sum = usd_current_e1_quote + usd_current_e2_quote
    usd_e1_quote_diff = usd_current_e1_quote - usd_start_e1_quote
    usd_e2_quote_diff = usd_current_e2_quote - usd_start_e2_quote
    e1_base_diff = current_e1_base - start_e1_base
    e2_base_diff = current_e2_base - start_e2_base

    current_timestamp = int(time.time())
    seconds_elapsed = current_timestamp - start_timestamp
    days_elapsed = seconds_elapsed / 60.0 / 60.0 / 24.0

    usd_profit = usd_e1_quote_diff + usd_e2_quote_diff
    usd_percent_profit = (usd_current_sum / usd_start_sum - ONE) * HUNDRED
    annualized_profit_ratio = (usd_current_sum / usd_start_sum) ** num_to_decimal(365 / days_elapsed)
    annualized_profit = (annualized_profit_ratio - ONE) * HUNDRED
    base_profit = e1_base_diff + e2_base_diff

    e1_usd_volume = convert_currencies(e1_quote, 'USD', e1_quote_volume)
    e2_usd_volume = convert_currencies(e2_quote, 'USD', e2_quote_volume)

    e1_name = capitalize(e1_name)
    e2_name = capitalize(e2_name)

    fancy_log('Start Balances')
    logging.info('{:<25} {}'.format(e1_base + ':', start_e1_base))
    logging.info('{:<25} {}'.format(e1_quote + ':', start_e1_quote))
    logging.info('{:<25} {}'.format(e2_base + ':', start_e2_base))
    logging.info('{:<25} {}'.format(e2_quote + ':', start_e2_quote))
    fancy_log('Current Balances')
    logging.info('{:<25} {}'.format(e1_base + ':', current_e1_base))
    logging.info('{:<25} {}'.format(e1_quote + ':', current_e1_quote))
    logging.info('{:<25} {}'.format(e2_base + ':', current_e2_base))
    logging.info('{:<25} {}'.format(e2_quote + ':', current_e2_quote))
    fancy_log('Balance Differences')
    logging.info('{:<25} {}'.format(e1_base + ':', current_e1_base - start_e1_base))
    logging.info('{:<25} {}'.format(e1_quote + ':', current_e1_quote - start_e1_quote))
    logging.info('{:<25} {}'.format(e2_base + ':', current_e2_base - start_e2_base))
    logging.info('{:<25} {}'.format(e2_quote + ':', current_e2_quote - start_e2_quote))
    fancy_log('Profitability, Current Forex')
    logging.info('{:<25} {}'.format('USD:', usd_profit))
    logging.info('{:<25} {}'.format('Percent (USD):', usd_percent_profit))
    logging.info('{:<25} {}'.format('Annualized (USD):', annualized_profit))
    logging.info('{:<25} {}'.format(e1_base + ':', base_profit))
    fancy_log('Trading Summary')
    logging.info('{:<25} {}'.format('Days run:', days_elapsed))
    logging.info('{:<25} {}'.format('Trade count:', trade_count))
    logging.info('{:<25} {}'.format(e1_name + ' base volume:', e1_base_volume))
    logging.info('{:<25} {}'.format(e1_name + ' quote volume:', e1_quote_volume))
    logging.info('{:<25} {}'.format(e1_name + ' usd volume:', e1_usd_volume))
    logging.info('{:<25} {}'.format(e2_name + ' base volume:', e2_base_volume))
    logging.info('{:<25} {}'.format(e2_name + ' quote volume:', e2_quote_volume))
    logging.info('{:<25} {}'.format(e2_name + ' usd volume:', e2_usd_volume))
    if e1_quote != 'USD' or e2_quote != 'USD':
        fancy_log('Forex')
        if e1_quote != 'USD':
            e1_current_rate = convert_currencies('USD', e1_quote, ONE)
            e1_rate_percent_change = (e1_current_rate / e1_start_rate - ONE) * HUNDRED
            logging.info('{:<25} {}'.format('Start ' + e1_quote + '/USD:', e1_start_rate))
            logging.info('{:<25} {}'.format('Current ' + e1_quote + '/USD:', e1_current_rate))
            logging.info('{:<25} {}'.format('Percent change:', e1_rate_percent_change))
        if e2_quote != 'USD':
            e2_current_rate = convert_currencies('USD', e2_quote, ONE)
            e2_rate_percent_change = (e2_current_rate / e2_start_rate - ONE) * HUNDRED
            logging.info('{:<25} {}'.format('Start ' + e2_quote + '/USD:', e2_start_rate))
            logging.info('{:<25} {}'.format('Current ' + e2_quote + '/USD:', e2_current_rate))
            logging.info('{:<25} {}'.format('Percent change:', e2_rate_percent_change))


if __name__ == "__main__":
    main()
