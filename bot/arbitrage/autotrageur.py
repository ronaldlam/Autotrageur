import getpass
import logging
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path

import ccxt
import schedule
import yaml
from dotenv import load_dotenv

import libs.db.maria_db_handler as db_handler
from bot.common.config_constants import (DB_NAME, DB_USER, DRYRUN,
                                         DRYRUN_E1_BASE, DRYRUN_E1_QUOTE,
                                         DRYRUN_E2_BASE, DRYRUN_E2_QUOTE,
                                         ENV_VAR_NAMES, EXCHANGE1,
                                         EXCHANGE1_PAIR, EXCHANGE1_TEST,
                                         EXCHANGE2, EXCHANGE2_PAIR,
                                         EXCHANGE2_TEST, SLIPPAGE)
from bot.common.notification_constants import (SUBJECT_DRY_RUN_FAILURE,
                                               SUBJECT_LIVE_FAILURE)
from bot.trader.ccxt_trader import CCXTTrader
from bot.trader.dry_run import DryRun, DryRunExchange
from libs.constants.ccxt_constants import API_KEY, API_SECRET, PASSWORD
from libs.security.encryption import decrypt
from libs.utilities import keyfile_to_map, num_to_decimal, to_bytes, to_str
from libs.utils.ccxt_utils import RetryableError, RetryCounter

# Program argument constants.
CONFIGFILE = "CONFIGFILE"
KEYFILE = "KEYFILE"

# Logging constants
START_END_FORMAT = "{} {:^15} {}"
STARS = "*"*20


def fancy_log(title):
    """Log title surrounded by stars."""
    logging.info(START_END_FORMAT.format(STARS, title, STARS))


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
            self.config = yaml.safe_load(ymlfile)

    def __load_db(self):
        """Initializes and connects to the database."""
        db_password = getpass.getpass(
            prompt="Enter database password:")
        db_handler.start_db(
            self.config[DB_USER],
            db_password,
            self.config[DB_NAME])
        schedule.every(7).hours.do(db_handler.ping_db)

    def __load_env_vars(self):
        """Ensures that the necessary environment variables are loaded.

        Returns:
            bool: True if the necessary environment variables have been loaded
                successfully.  Else, False."""
        env_path = Path('.env')
        env_vars_loaded = (
            env_path.exists() and load_dotenv(dotenv_path=env_path))

        # Check if the necessary variables are loaded.
        if env_vars_loaded:
            for env_var_name in ENV_VAR_NAMES:
                if not os.getenv(env_var_name):
                    env_vars_loaded = False
        return env_vars_loaded

    def __load_keyfile(self, arguments):
        """Load the keyfile given in the arguments.

        Prompts user for a passphrase to decrypt the encrypted keyfile.

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
            pw = getpass.getpass(prompt="Enter keyfile password:")
            with open(arguments[KEYFILE], "rb") as in_file:
                keys = decrypt(
                    in_file.read(),
                    to_bytes(pw),
                    arguments['--pi-mode'])

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
        # Load environment variables.
        if not self.__load_env_vars():
            raise EnvironmentError('Failed to load all of the necessary'
                                   ' environment variables.')

        # Load arb configuration.
        self.__load_config_file(arguments[CONFIGFILE])

        # Initialize and connect to the database.
        self.__load_db()

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
            self.exchange1_configs['password'] = (
                exchange_key_map[self.config[EXCHANGE1]][PASSWORD])
            self.exchange2_configs['apiKey'] = (
                exchange_key_map[self.config[EXCHANGE2]][API_KEY])
            self.exchange2_configs['secret'] = (
                exchange_key_map[self.config[EXCHANGE2]][API_SECRET])
            self.exchange2_configs['password'] = (
                exchange_key_map[self.config[EXCHANGE2]][PASSWORD])

    def _setup(self):
        """Sets up the algorithm to use."""
        # Extract the pairs and compare them to see if conversion needed to
        # USD.
        e1_base, e1_quote = self.config[EXCHANGE1_PAIR].upper().split("/")
        e2_base, e2_quote = self.config[EXCHANGE2_PAIR].upper().split("/")

        exchange1 = self.config[EXCHANGE1]
        exchange2 = self.config[EXCHANGE2]

        # Create dry run objects to hold dry run state.
        if self.config[DRYRUN]:
            e1_base_balance = self.config[DRYRUN_E1_BASE]
            e1_quote_balance = self.config[DRYRUN_E1_QUOTE]
            e2_base_balance = self.config[DRYRUN_E2_BASE]
            e2_quote_balance = self.config[DRYRUN_E2_QUOTE]
            dry_e1 = DryRunExchange(exchange1, e1_base, e1_quote,
                                    e1_base_balance, e1_quote_balance)
            dry_e2 = DryRunExchange(exchange2, e2_base, e2_quote,
                                    e2_base_balance, e2_quote_balance)
            self.dry_run = DryRun(dry_e1, dry_e2)
        else:
            dry_e1 = None
            dry_e2 = None
            self.dry_run = None

        self.trader1 = CCXTTrader(
            e1_base,
            e1_quote,
            exchange1,
            num_to_decimal(self.config[SLIPPAGE]),
            self.exchange1_configs,
            dry_e1)
        self.trader2 = CCXTTrader(
            e2_base,
            e2_quote,
            exchange2,
            num_to_decimal(self.config[SLIPPAGE]),
            self.exchange2_configs,
            dry_e2)

        # Connect to test API's if required
        if self.config[EXCHANGE1_TEST]:
            self.trader1.connect_test_api()
        if self.config[EXCHANGE2_TEST]:
            self.trader2.connect_test_api()

        # Load the available markets for the exchange.
        self.trader1.load_markets()
        self.trader2.load_markets()

    @abstractmethod
    def _alert(self, subject, exception):
        """Last ditch effort to alert user on operation failure.

        Args:
            subject (str): The subject/topic for the alert.
            exception (Exception): The exception to alert about.
        """
        pass

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

    def run_autotrageur(self, arguments, requires_configs=True):
        """Run Autotrageur algorithm.

        During dry run operation, the 'while True' loop will loop
        indefinitely until a keyboard interrupt, after which the
        exchange data will be summarized and the program will exit.

        When the program is started with live trading, exceptions raised
        will be caught and a dry run will be started. We expect the
        issue to be reported through the email mechanism in
        fcf_autotrageur. Note that this does not apply to the keyboard
        interrupt, which will exit the program directly.

        Args:
            arguments (map): Map of command line arguments.
            requires_configs (bool, optional): Defaults to True. Whether
                the call requires the config file to be loaded.
        """
        if requires_configs:
            self._load_configs(arguments)

        self._setup()
        retry_counter = RetryCounter()

        try:
            while True:
                try:
                    schedule.run_pending()
                    self._clean_up()
                    fancy_log("Start Poll")
                    if self._poll_opportunity():
                        fancy_log("End Poll")
                        fancy_log("Start Trade")
                        self._execute_trade()
                        fancy_log("End Trade")
                    else:
                        fancy_log("End Poll")
                    retry_counter.increment()
                    self._wait()
                except RetryableError as e:
                    logging.error(e, exc_info=True)
                    if retry_counter.decrement():
                        self._wait()
                    else:
                        raise
        except KeyboardInterrupt:
            if self.config[DRYRUN]:
                logging.critical("Keyboard Interrupt")
                fancy_log("Summary")
                self.dry_run.log_all()
                fancy_log("End")
            else:
                raise
        except Exception as e:
            if not self.config[DRYRUN]:
                logging.critical("Falling back to dry run, error encountered:")
                logging.critical(e)
                self._alert(SUBJECT_LIVE_FAILURE, e)
                self.config[DRYRUN] = True
                self.run_autotrageur(arguments, False)
            else:
                self._alert(SUBJECT_DRY_RUN_FAILURE, e)
                raise
