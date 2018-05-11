import logging
import time
from abc import ABC, abstractmethod

import ccxt
import yaml

from libs.security.encryption import decrypt
from libs.utilities import keyfile_to_map, to_bytes, to_str
from bot.common.config_constants import (DRYRUN, SLIPPAGE, EXCHANGE1,
    EXCHANGE2, EXCHANGE1_PAIR, EXCHANGE2_PAIR, EXCHANGE1_TEST, EXCHANGE2_TEST,
    TARGET_AMOUNT)
from bot.common.ccxt_exchange_constants import API_KEY, API_SECRET

from bot.trader.ccxt_trader import CCXTTrader


# Program argument constants.
CONFIGFILE = "CONFIGFILE"
KEYFILE = "KEYFILE"
PASSWORD = "PASSWORD"
SALT = "SALT"


class AuthenticationError(Exception):
    """Incorrect credentials or exchange unavailable."""
    pass


class Autotrageur(ABC):
    """Base class for running Autotrageur, the algorithmic trading bot.

    This class follows the "Template Method" design pattern. The
    functions prefixed with _ are functionally protected methods, and
    should only be called inside this class or its subclasses. The
    run_autotrageur() function is used as the template method to run the
    trading algorithm. Subclasses should override the protected methods
    to alter behaviour and run different algorithms with different
    configurations.
    """

    def __load_config_file(self, file_name):
        """Load the given config file.

        Args:
            file_name (str): The name of the file.
        """
        with open(file_name, "r") as ymlfile:
            self.config = yaml.load(ymlfile)

    def __load_keyfile(self, arguments):
        """Load the keyfile given in the arguments.

        Args:
            arguments (dict): Map of the arguments passed to the program.

        Raises:
            IOError: If the encrypted keyfile does not open, and not in
                dryrun mode.

        Returns:
            dict: Map of the keyfile contents, or None if dryrun and
                unavailable.
        """
        try:
            with open(arguments[KEYFILE], "rb") as in_file:
                keys = decrypt(
                    in_file.read(),
                    to_bytes(arguments[PASSWORD]),
                    to_bytes(arguments[SALT]))

            str_keys = to_str(keys)
            return keyfile_to_map(str_keys)
        except Exception:
            logging.error("Unable to load keyfile.", exc_info=True)
            if not self.config[DRYRUN]:
                raise IOError("Unable to open file. %s" % arguments)
            else:
                logging.info("**Dry run: continuing with program")
                return None

    def _load_configs(self, arguments):
        """Load the configurations of the Autotrageur run.

        Args:
            arguments (dict): Map of the arguments passed to the program.

        Raises:
            IOError: If the encrypted keyfile does not open, and not in
                dryrun mode.
        """
        # Load arb configuration.
        self.__load_config_file(arguments[CONFIGFILE])

        # Load keyfile.
        exchange_key_map = self.__load_keyfile(arguments)

        # Get exchange configuration settings.
        self.exchange1_configs = {
            "nonce": ccxt.Exchange.milliseconds
        }
        self.exchange2_configs = {
            "nonce": ccxt.Exchange.milliseconds
        }

        if exchange_key_map:
            self.exchange1_configs['apiKey'] = (
                exchange_key_map[self.config[EXCHANGE1]][API_KEY])
            self.exchange1_configs['secret'] = (
                exchange_key_map[self.config[EXCHANGE1]][API_SECRET])
            self.exchange2_configs['apiKey'] = (
                exchange_key_map[self.config[EXCHANGE2]][API_KEY])
            self.exchange2_configs['secret'] = (
                exchange_key_map[self.config[EXCHANGE2]][API_SECRET])

    def _setup_markets(self):
        """Set up the market objects for the algorithm to use.

        Raises:
            AuthenticationError: If not dryrun and authentication fails.
        """
        # Extract the pairs and compare them to see if conversion needed to
        # USD.
        self.exchange1_basequote = self.config[EXCHANGE1_PAIR].split("/")
        self.exchange2_basequote = self.config[EXCHANGE2_PAIR].split("/")

        self.tclient1 = CCXTTrader(
            self.exchange1_basequote[0],
            self.exchange1_basequote[1],
            self.config[EXCHANGE1],
            self.config[SLIPPAGE],
            self.config[TARGET_AMOUNT],
            self.exchange1_configs,
            self.config[DRYRUN])
        self.tclient2 = CCXTTrader(
            self.exchange2_basequote[0],
            self.exchange2_basequote[1],
            self.config[EXCHANGE2],
            self.config[SLIPPAGE],
            self.config[TARGET_AMOUNT],
            self.exchange2_configs,
            self.config[DRYRUN])

        # Connect to test API's if required
        if self.config[EXCHANGE1_TEST]:
            self.tclient1.connect_test_api()
        if self.config[EXCHANGE2_TEST]:
            self.tclient2.connect_test_api()

        # Load the available markets for the exchange.
        self.tclient1.load_markets()
        self.tclient2.load_markets()

        # NOTE: Assumes the quote pair is 'USD' or 'USDT' for V1.
        for tclient in list((self.tclient1, self.tclient2)):
            if (tclient.quote != 'USD') and (tclient.quote != 'USDT'):
                tclient.set_conversion_needed(True)

        try:
            self.tclient1.check_wallet_balances()
            self.tclient2.check_wallet_balances()
        except (ccxt.AuthenticationError, ccxt.ExchangeNotAvailable) as auth_error:
            logging.error(auth_error)

            # If configuration is set for a dry run, continue the program even
            # with wrong auth credentials.
            if self.config[DRYRUN]:
                logging.info("**Dry run: continuing with program")
            else:
                raise AuthenticationError(auth_error)

    @abstractmethod
    def _poll_opportunity(self):
        """Poll exchanges for arbitrage opportunity.

        Returns:
            bool: Whether there is an opportunity.
        """
        pass

    @abstractmethod
    def _execute_trade(self):
        """Execute the trade, providing necessary failsafes."""
        pass

    @abstractmethod
    def _clean_up(self):
        """Cleans up the state of the autotrageur."""
        pass

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
            self._clean_up()
            if self._poll_opportunity():
                self._execute_trade()
            self._wait()
