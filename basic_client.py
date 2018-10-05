"""Basic Client to interface with crypto exchanges.

NOT to be used with production.  Make sure to run with `python -i ...` to run
in interactive mode, or double-check the source code alterations at the
main function.  Some examples are provided at the bottom of the file.

Usage:
    basic_client.py KEYFILE EXCHANGE [--pi_mode] [--test_api] [--verbose]

Options:
    --pi_mode                           Whether this is to be used with the raspberry pi or on a full desktop.
    --test_api                          Whether to use the exchange's test API.
    --verbose                           Whether to provide verbose logging from ccxt's network calls.

Description:
    KEYFILE                             The encrypted Keyfile containing relevant api keys.
    EXCHANGE                            The name of the exchange you wish to interact with.
"""
import getpass
import logging
import pprint

import ccxt
from docopt import docopt

import libs.ccxt_extensions as ccxt_extensions
from libs.constants.ccxt_constants import API_KEY, API_SECRET
from libs.security.encryption import decrypt
from libs.utilities import keyfile_to_map, num_to_decimal, to_bytes, to_str


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")


# Constants
EXTENSION_PREFIX = "ext_"
EXCHANGE = 'EXCHANGE'
KEYFILE = 'KEYFILE'


def load_keyfile(keyfile, pi_mode=False):
        """Load the keyfile given in the arguments.

        Returns:
            dict: Map of the keyfile contents, or None if dryrun and
                unavailable.
        """
        pw = getpass.getpass(prompt="Enter keyfile password:")
        with open(keyfile, "rb") as in_file:
            keys = decrypt(
                in_file.read(),
                to_bytes(pw),
                pi_mode)

        str_keys = to_str(keys)
        return keyfile_to_map(str_keys)


def load_exchange(exchange_name, keyfile, pi_mode=False, use_test_api=False,
                  use_verbose=False):
    """Load the exchange given from user input.

    Also calls `load_markets()` to ensure that the ccxt exchange object has been
    initialized.

    Args:
        exchange_name (str): Name of the exchange to load.
        keyfile (str): Name of the keyfile to obtain api keys.
        pi_mode (bool): Whether to run Scrypt with memory limitations to
            accommodate raspberry pi.  Default is False.
        use_test_api (bool): Whether to use an exchange's test API.
            Default is False.
        use_verbose (bool): Whether to output ccxt's verbose logging from
            network calls.  Default is False.

    Raises:
        IOError: If the encrypted keyfile does not open, and not in
            dryrun mode.
    """
    # Load keyfile.
    exchange_key_map = load_keyfile(keyfile, pi_mode)

    # Exchange configuration settings.
    exchange_config = {
        'nonce': ccxt.Exchange.milliseconds,
        'verbose': use_verbose
    }

    if exchange_key_map:
        exchange_config['apiKey'] = (
            exchange_key_map[exchange_name][API_KEY])
        exchange_config['secret'] = (
            exchange_key_map[exchange_name][API_SECRET])
        exchange_config['password'] = (
            exchange_key_map[exchange_name][API_SECRET])

    if EXTENSION_PREFIX + exchange_name in dir(ccxt_extensions):
        ccxt_exchange = getattr(
            ccxt_extensions, EXTENSION_PREFIX + exchange_name)(exchange_config)
    else:
        ccxt_exchange = getattr(ccxt, exchange_name)(exchange_config)

    # Connect to Test exchange, if requested.
    if use_test_api:
        if 'test' in ccxt_exchange.urls:
            ccxt_exchange.urls['api'] = ccxt_exchange.urls['test']
        else:
            raise NotImplementedError(
                "Test connection to %s not implemented." %
                exchange_name)

    load_markets_result = ccxt_exchange.load_markets()
    logging.info(pprint.pformat(load_markets_result))
    return ccxt_exchange

if __name__ == "__main__":
    args = docopt(__doc__, version="BasicClient 0.1")

    exchange = load_exchange(
        args[EXCHANGE], args[KEYFILE], args['--pi_mode'], args['--test_api'],
        args['--verbose'])
    logging.info(
        'Loaded exchange: {}.  Ensure that there is ample exchange data output'
        ' displayed or call `exchange.load_markets()` to see available markets'
        ' and test connection.'.format(exchange.name))
    logging.info(
        'If you have run interactively, you can now interact with ccxt directly.')

# General - basic example fetch wallet balances
"""
balances = exchange.fetch_balance()
print(pprint.pformat(balances))
"""

# Kraken - example with generated methods in ccxt.
"""
print(json.dumps(exchange.privatePostTradeBalance({
    'aclass': 'currency',
    'asset': 'BTC'
})))
"""

# Kraken - example with basic market buy order.
"""
buy_result = exchange.create_market_buy_order('ETH/USD', num_to_decimal('0.02'))
print(buy_result)
"""

# Gemini examples - emulated market orders with Autotrageur custom `ext_`
# exchange objects.
"""
resp = exchange.create_emulated_market_sell_order('ETH/USD',
    num_to_decimal(400), num_to_decimal(0.001), 3)
resp = exchange.create_emulated_market_buy_order('ETH/USD',
    num_to_decimal(40), num_to_decimal(400), 3)
print(resp)

oid = '97580675'    # The `resp['id']`
resp = exchange.fetch_my_trades('ETH/USD')
for order in resp:
    if order['order'] == oid:
        print("Matching Order!")
        print(order)
"""
