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
import logging
import pprint

import ccxt
from docopt import docopt

from autotrageur.version import VERSION
from fp_libs.ccxt_extensions.exchange_loader import load_exchange
from fp_libs.utilities import load_keyfile, num_to_decimal, to_bytes, to_str

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")


# Constants
EXTENSION_PREFIX = "ext_"
EXCHANGE = 'EXCHANGE'
KEYFILE = 'KEYFILE'


if __name__ == "__main__":
    args = docopt(__doc__, version=VERSION)

    # Load keyfile.
    exchange_key_map = load_keyfile(args[KEYFILE], args['--pi_mode'])

    exchange = load_exchange(
        args[EXCHANGE], exchange_key_map, args['--test_api'],
        args['--verbose'])

    load_markets_result = exchange.load_markets()
    logging.info(pprint.pformat(load_markets_result))

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
