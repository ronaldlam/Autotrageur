"""Automated arbitrageur

Executes trades based on simple arbitrage strategy

Usage:
    autotrageur.py KEYFILE PASSWORD SALT CONFIGFILE
"""

import ccxt
from docopt import docopt
import yaml

from libs.security.utils import decrypt, keyfile_to_map, to_bytes, to_str
from bot.orderbook_processor import get_price_from_orderbook

KEYFILE = "KEYFILE"
PASSWORD = "PASSWORD"
SALT = "SALT"

CONFIG_FILE = "arb_config.yaml"
EXCHANGE1 = "exchange1"
EXCHANGE2 = "exchange2"
EXCHANGE1_PAIR = "exchange1_pair"
EXCHANGE2_PAIR = "exchange2_pair"

API_KEY = "api_key"
API_SECRET = "api_secret"

SPREAD_TARGET_LOW = "spread_target_low"
SPREAD_TARGET_HIGH = "spread_target_high"

BIDS = "bids"
ASKS = "asks"

if __name__ == "__main__":
    arguments = docopt(__doc__, version="Autotrageur 0.1")
    keys = None

    with open(arguments[KEYFILE], "rb") as in_file:
        keys = decrypt(
            in_file.read(),
            to_bytes(arguments[PASSWORD]),
            to_bytes(arguments[SALT]))

    if keys is None:
        raise IOError("Unable to open file. %s" % arguments)

    str_keys = to_str(keys)
    exchange_key_map = keyfile_to_map(str_keys)

    with open(CONFIG_FILE, "r") as ymlfile:
        config = yaml.load(ymlfile)

    exchange1_configs = {
        "apiKey": exchange_key_map[config[EXCHANGE1]][API_KEY],
        "secret": exchange_key_map[config[EXCHANGE1]][API_SECRET],
        "verbose": False,
    }

    exchange2_configs = {
        "apiKey": exchange_key_map[config[EXCHANGE2]][API_KEY],
        "secret": exchange_key_map[config[EXCHANGE2]][API_SECRET],
        "verbose": False,
    }

    exchange1 = getattr(ccxt, config[EXCHANGE1])(exchange1_configs)
    exchange2 = getattr(ccxt, config[EXCHANGE2])(exchange2_configs)

    spread_low = config[SPREAD_TARGET_LOW]
    spread_high = config[SPREAD_TARGET_HIGH]

    exchange1_orderbook = exchange1.fetch_order_book(config[EXCHANGE1_PAIR])
    exchange1_bids = exchange1_orderbook[BIDS]
    exchange1_asks = exchange1_orderbook[ASKS]

    exchange2_orderbook = exchange2.fetch_order_book(config[EXCHANGE2_PAIR])
    exchange2_bids = exchange2_orderbook[BIDS]
    exchange2_asks = exchange2_orderbook[ASKS]

    # Hardcoded for now, currently calcs instantaneous rates
    fiat_limit = 50000
    exchange1_buy = get_price_from_orderbook(exchange1_asks, fiat_limit)
    exchange1_sell = get_price_from_orderbook(exchange1_bids, fiat_limit)
    exchange2_buy = get_price_from_orderbook(exchange2_asks, fiat_limit)
    exchange2_sell = get_price_from_orderbook(exchange2_bids, fiat_limit)

    print("%s buy of %d, %s price: %.2f" %
          (config[EXCHANGE1], fiat_limit, config[EXCHANGE1_PAIR], exchange1_buy))
    print("%s buy of %d, %s price: %.2f" %
          (config[EXCHANGE2], fiat_limit, config[EXCHANGE2_PAIR], exchange2_buy))
    print("%s sell of %d, %s price: %.2f" %
          (config[EXCHANGE1], fiat_limit, config[EXCHANGE1_PAIR], exchange1_sell))
    print("%s sell of %d, %s price: %.2f" %
          (config[EXCHANGE2], fiat_limit, config[EXCHANGE2_PAIR], exchange2_sell))
