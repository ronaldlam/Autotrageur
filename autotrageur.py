"""Automated arbitrageur

Executes trades based on simple arbitrage strategy

Usage:
    autotrageur.py KEYFILE PASSWORD SALT CONFIGFILE
"""

import logging
import time

import ccxt
from docopt import docopt
import yaml

from libs.security.utils import decrypt, keyfile_to_map, to_bytes, to_str
from libs.email_client.simple_email_client import send_all_emails
import bot.arbitrage.arbseeker as arbseeker
import bot.datafetcher.realtimeapiclient as realtimeapiclient

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

# For debugging purposes.
logging.basicConfig(level=logging.DEBUG)

# Hardcoded for now, currently calcs instantaneous rates
TARGET_AMOUNT = 50000

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

    # Get exchange configuration settings.
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

    # Get spread low and highs.
    spread_low = config[SPREAD_TARGET_LOW]
    spread_high = config[SPREAD_TARGET_HIGH]

    # Extract the pairs and compare them to see if conversion needed to USD.
    exchange1_basequote = config[EXCHANGE1_PAIR].split("/")
    exchange2_basequote = config[EXCHANGE2_PAIR].split("/")

    rtclient_exchange1 = realtimeapiclient.RealTimeAPIClient(
        exchange1_basequote[0], exchange1_basequote[1], config[EXCHANGE1],
        exchange1_configs)
    rtclient_exchange2 = realtimeapiclient.RealTimeAPIClient(
        exchange2_basequote[0], exchange2_basequote[1], config[EXCHANGE2],
        exchange2_configs)

    # NOTE: Assumes the quote pair is fiat or stablecoin for V1.
    for rtclient in list((rtclient_exchange1, rtclient_exchange2)):
        if (rtclient.quote != 'USD') and (rtclient.quote != 'USDT'):
            rtclient.set_conversion_needed(True)

    # Continuously poll to obtains spread opportunities.  Sends an e-mail when
    # spread_high or spread_low targets are hit.
    # TODO: Prepare a market buy/sell order to exchanges, awaiting user
    # confirmation.
    while(True):
        spread_opp = arbseeker.get_arb_opportunities_by_orderbook(rtclient_exchange1,
            rtclient_exchange2, spread_low, spread_high, TARGET_AMOUNT)
        if spread_opp is not None:
            send_all_emails("Subject: Arb Forward-Spread Alert!\nThe spread of "
                            + exchange1_basequote[0]
                            + " is "
                            + str(spread_opp['spread']))
        time.sleep(5)
