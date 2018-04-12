import logging
import time

import ccxt
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


class Autotrageur:
    """Base class for running Autotrageur, the algorithmic trading bot.

    This class follows the "Template Method" design pattern. The
    functions prefixed with _ are functionally protected methods, and
    should only be called inside this class or its subclasses. The
    run_autotrageur() function is used as the template method to run the
    trading algorithm. Subclasses should override the protected methods
    to alter behaviour and run different algorthims with different
    configurations.
    """

    def _load_configs(self, arguments):
        """Load the configurations of the Autotrageur run.

        Args:
            arguments (map): Map of the arguments passed to the program

        Raises:
            IOError: If the encrypted keyfile does not open.
        """

        # Load keyfile
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
            self.config = yaml.load(ymlfile)

        # Get exchange configuration settings.
        if self.config[AUTHENTICATE]:
            self.exchange1_configs = {
                "apiKey": exchange_key_map[self.config[EXCHANGE1]][API_KEY],
                "secret": exchange_key_map[self.config[EXCHANGE1]][API_SECRET],
                "verbose": False,
            }
            self.exchange2_configs = {
                "apiKey": exchange_key_map[self.config[EXCHANGE2]][API_KEY],
                "secret": exchange_key_map[self.config[EXCHANGE2]][API_SECRET],
                "verbose": False,
            }
        else:
            self.exchange1_configs = {}
            self.exchange2_configs = {}

    def _setup_markets(self):
        """Set up the market objects for the algorithm to use."""

        # Extract the pairs and compare them to see if conversion needed to
        # USD.
        self.exchange1_basequote = self.config[EXCHANGE1_PAIR].split("/")
        self.exchange2_basequote = self.config[EXCHANGE2_PAIR].split("/")

        self.tclient_exchange1 = trading_client.TradingClient(
            self.exchange1_basequote[0],
            self.exchange1_basequote[1],
            self.config[EXCHANGE1],
            self.config[SLIPPAGE],
            self.config[TARGET_AMOUNT],
            self.exchange1_configs)
        self.tclient_exchange2 = trading_client.TradingClient(
            self.exchange2_basequote[0],
            self.exchange2_basequote[1],
            self.config[EXCHANGE2],
            self.config[SLIPPAGE],
            self.config[TARGET_AMOUNT],
            self.exchange2_configs)

        # Connect to test API's if required
        if self.config[EXCHANGE1_TEST]:
            self.tclient_exchange1.connect_test_api()
        if self.config[EXCHANGE2_TEST]:
            self.tclient_exchange2.connect_test_api()

        # NOTE: Assumes the quote pair is fiat or stablecoin for V1.
        for tclient in list((self.tclient_exchange1, self.tclient_exchange2)):
            if (tclient.quote != 'USD') and (tclient.quote != 'USDT'):
                tclient.set_conversion_needed(True)

        if self.config[AUTHENTICATE]:
            ex1_balance = self.tclient_exchange1.fetch_free_balance(
                self.exchange1_basequote[0])
            logging.log(logging.INFO,
                "Balance of %s on %s: %s" % (
                    self.exchange1_basequote[0],
                    self.config[EXCHANGE1],
                    ex1_balance))
            ex2_balance = self.tclient_exchange2.fetch_free_balance(
                self.exchange2_basequote[0])
            logging.log(logging.INFO,
                "Balance of %s on %s: %s" % (
                    self.exchange2_basequote[0],
                    self.config[EXCHANGE2],
                    ex2_balance))

    def _poll_opportunity(self):
        """Poll exchanges for arbitrage opportunity.

        Returns:
            bool: Whether there is an opportunity.
        """
        try:
            # Get spread low and highs.
            spread_low = self.config[SPREAD_TARGET_LOW]
            spread_high = self.config[SPREAD_TARGET_HIGH]
            self.spread_opp = arbseeker.get_arb_opportunities_by_orderbook(
                self.tclient_exchange1, self.tclient_exchange2, spread_low,
                spread_high)
        except ccxt.RequestTimeout as timeout:
            logging.error(timeout)
            return False
        finally:
            if self.spread_opp is None:
                self.message = "No arb opportunity found."
                logging.log(logging.INFO, self.message)
                return False
            elif self.spread_opp[arbseeker.SPREAD_HIGH]:
                self.message = (
                    "Subject: Arb Forward-Spread Alert!\nThe spread of "
                    + self.exchange1_basequote[0]
                    + " is "
                    + str(self.spread_opp[arbseeker.SPREAD]))
            else:
                self.message = (
                    "Subject: Arb Backward-Spread Alert!\nThe spread of "
                    + self.exchange1_basequote[0]
                    + " is "
                    + str(self.spread_opp[arbseeker.SPREAD]))
            return True

    def _execute_trade(self):
        """Execute the trade, providing necessary failsafes."""
        try:
            if self.config[AUTHENTICATE]:
                logging.info(self.message)
                send_all_emails(self.message)
                verify = input("Type 'execute' to attept trade execution")

                if verify == "execute":
                    logging.info("Attempting to execute trades")
                    arbseeker.execute_arbitrage(self.spread_opp)
                else:
                    logging.info("Trade was not executed.")
        except ccxt.RequestTimeout as timeout:
            logging.error(timeout)
        except arbseeker.AbortTradeException as abort_trade:
            logging.error(abort_trade)

    def _wait(self):
        """Wait for the specified polling interval."""
        time.sleep(5)

    def run_autotrageur(self, arguments):
        """Run Autotrageur algorithm.

        Args:
            arguments (map): Map of command line arguments.
        """

        self._load_configs(arguments)
        self._setup_markets()

        while True:
            if self._poll_opportunity():
                self._execute_trade()
            self._wait()
