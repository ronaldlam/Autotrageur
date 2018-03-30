"""Automated arbitrageur

Executes trades based on simple arbitrage strategy

Usage:
    autotrageur.py KEYFILE PASSWORD SALT CONFIGFILE
"""

import logging
import time

import ccxt
from ccxt.base.errors import RequestTimeout  # pylint: disable=E0611
from docopt import docopt
import yaml

from libs.security.utils import decrypt, keyfile_to_map, to_bytes, to_str
from libs.email_client.simple_email_client import send_all_emails
import bot.arbitrage.arbseeker as arbseeker
import bot.datafetcher.tradingapiclient as trading_client

KEYFILE = "KEYFILE"
PASSWORD = "PASSWORD"
SALT = "SALT"

CONFIG_FILE = "arb_config.yaml"
AUTHENTICATE = "authenticate"
SLIPPAGE = "slippage"
EXCHANGE1 = "exchange1"
EXCHANGE2 = "exchange2"
EXCHANGE1_PAIR = "exchange1_pair"
EXCHANGE2_PAIR = "exchange2_pair"
EXCHANGE1_TEST = "exchange1_test"
EXCHANGE2_TEST = "exchange2_test"

API_KEY = "api_key"
API_SECRET = "api_secret"

SPREAD_TARGET_LOW = "spread_target_low"
SPREAD_TARGET_HIGH = "spread_target_high"

TARGET_AMOUNT = "target_amount"

# For debugging purposes.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")

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
    if config[AUTHENTICATE]:
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
    else:
        exchange1_configs = {}
        exchange2_configs = {}

    # Get spread low and highs.
    spread_low = config[SPREAD_TARGET_LOW]
    spread_high = config[SPREAD_TARGET_HIGH]

    # Extract the pairs and compare them to see if conversion needed to USD.
    exchange1_basequote = config[EXCHANGE1_PAIR].split("/")
    exchange2_basequote = config[EXCHANGE2_PAIR].split("/")

    tclient_exchange1 = trading_client.TradingClient(
        exchange1_basequote[0],
        exchange1_basequote[1],
        config[EXCHANGE1],
        config[SLIPPAGE],
        config[TARGET_AMOUNT],
        exchange1_configs)
    tclient_exchange2 = trading_client.TradingClient(
        exchange2_basequote[0],
        exchange2_basequote[1],
        config[EXCHANGE2],
        config[SLIPPAGE],
        config[TARGET_AMOUNT],
        exchange2_configs)

    # Connect to test API's if required
    if config[EXCHANGE1_TEST]:
        tclient_exchange1.connect_test_api()
    if config[EXCHANGE2_TEST]:
        tclient_exchange2.connect_test_api()

    # NOTE: Assumes the quote pair is fiat or stablecoin for V1.
    for rtclient in list((tclient_exchange1, tclient_exchange2)):
        if (rtclient.quote != 'USD') and (rtclient.quote != 'USDT'):
            rtclient.set_conversion_needed(True)

    if config[AUTHENTICATE]:
        ex1_balance = tclient_exchange1.fetch_free_balance(
            exchange1_basequote[0])
        logging.log(logging.INFO, "Balance of %s on %s: %s" %
                    (exchange1_basequote[0], config[EXCHANGE1], ex1_balance))
        ex2_balance = tclient_exchange2.fetch_free_balance(
            exchange2_basequote[0])
        logging.log(logging.INFO, "Balance of %s on %s: %s" %
                    (exchange2_basequote[0], config[EXCHANGE2], ex2_balance))

    # Continuously poll to obtain spread opportunities.  Sends an e-mail when
    # spread_high or spread_low targets are hit.
    while True:
        try:
            spread_opp = arbseeker.get_arb_opportunities_by_orderbook(
                tclient_exchange1, tclient_exchange2, spread_low,
                spread_high)
            if spread_opp is None:
                message = "No arb opportunity found."
                logging.log(logging.INFO, message)
                raise arbseeker.AbortTradeException(message)
            elif spread_opp[arbseeker.SPREAD_HIGH]:
                message = (
                    "Subject: Arb Forward-Spread Alert!\nThe spread of "
                            + exchange1_basequote[0]
                            + " is "
                            + str(spread_opp[arbseeker.SPREAD]))
            else:
                message = (
                    "Subject: Arb Backward-Spread Alert!\nThe spread of "
                            + exchange1_basequote[0]
                            + " is "
                            + str(spread_opp[arbseeker.SPREAD]))

            if config[AUTHENTICATE]:
                logging.info(message)
                send_all_emails(message)
                verify = input("Type 'execute' to attept trade execution")

                if verify == "execute":
                    logging.info("Attempting to execute trades")
                    arbseeker.execute_arbitrage(spread_opp)
                else:
                    logging.info("Trade was not executed.")

        except RequestTimeout as timeout:
            logging.error(timeout)
        except arbseeker.AbortTradeException as abort_trade:
            logging.error(abort_trade)
        finally:
            time.sleep(5)
