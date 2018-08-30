import getpass
import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from collections import namedtuple
from pathlib import Path

import ccxt
import schedule
import yaml
from dotenv import load_dotenv

import libs.db.maria_db_handler as db_handler
from bot.common.env_var_constants import ENV_VAR_NAMES
from bot.common.notification_constants import (SUBJECT_DRY_RUN_FAILURE,
                                               SUBJECT_LIVE_FAILURE)
from bot.trader.ccxt_trader import CCXTTrader
from bot.trader.dry_run import DryRun, DryRunExchange
from libs.constants.ccxt_constants import API_KEY, API_SECRET, PASSWORD
from libs.security.encryption import decrypt
from libs.utilities import (keyfile_to_map, num_to_decimal, split_symbol,
                            to_bytes, to_str)
from libs.utils.ccxt_utils import RetryableError, RetryCounter

# Program argument constants.
CONFIGFILE = "CONFIGFILE"
KEYFILE = "KEYFILE"

# Logging constants
START_END_FORMAT = "{} {:^15} {}"
STARS = "*"*20


class Configuration(namedtuple('Configuration', [
        'db_name', 'db_user', 'dryrun', 'dryrun_e1_base', 'dryrun_e1_quote',
        'dryrun_e2_base', 'dryrun_e2_quote', 'email_cfg_path', 'exchange1',
        'exchange1_pair', 'exchange1_test', 'exchange2',
        'exchange2_pair', 'exchange2_test', 'h_to_e1_max', 'h_to_e2_max', 'id',
        'slippage', 'spread_min', 'start_timestamp', 'twilio_cfg_path',
        'vol_min'])):
    """Holds all of the configuration for the autotrageur bot.

    Args:
    #TODO comments
        spread_opp (SpreadOpportunity): The spread opportunity to
            consider.

    """
    __slots__ = ()


class AsymmetricTestExchangeConfigError(Exception):
    """Raised when one exchange has enabled trading against a test API and the
    other has not."""
    pass

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

    def __parse_config_file(self, file_name):
        """Load the given config file.

        Args:
            file_name (str): The name of the file.
        """
        with open(file_name, 'r') as ymlfile:
            return yaml.safe_load(ymlfile)

    def __init_db(self):
        """Initializes and connects to the database."""
        db_password = getpass.getpass(
            prompt="Enter database password:")
        db_handler.start_db(
            self._config.db_user,
            db_password,
            self._config.db_name)
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

    def __parse_keyfile(self, keyfile_path, pi_mode=False):
        """Parses the keyfile given in the arguments.

        Prompts user for a passphrase to decrypt the encrypted keyfile.

        Args:
            keyfile_path (str): The path to the keyfile.
            pi_mode (bool): Whether to decrypt with memory limitations to
                accommodate raspberry pi.  Default is False.

        Raises:
            IOError: If the encrypted keyfile does not open, and not in
                dryrun mode.

        Returns:
            dict: Map of the keyfile contents, or None if dryrun and
                unavailable.
        """
        try:
            pw = getpass.getpass(prompt="Enter keyfile password:")
            with open(keyfile_path, "rb") as in_file:
                keys = decrypt(
                    in_file.read(),
                    to_bytes(pw),
                    pi_mode=pi_mode)

            str_keys = to_str(keys)
            return keyfile_to_map(str_keys)
        except Exception:
            logging.error("Unable to load keyfile.", exc_info=True)
            if not self._config.dryrun:
                raise IOError("Unable to open file: %s" % keyfile_path)
            else:
                logging.info("**Dry run: continuing with program")
                return None


    def __setup_traders(self, exchange_key_map):
        # TODO: Comments
        # TODO: Looks suitable for a Builder pattern here to create the Traders
        # as their creation is complex enough.

        # Extract the pairs and compare them to see if conversion needed to
        # USD.
        e1_base, e1_quote = split_symbol(self._config.exchange1_pair)
        e2_base, e2_quote = split_symbol(self._config.exchange2_pair)

        exchange1 = self._config.exchange1
        exchange2 = self._config.exchange2

        # Create dry run objects to hold dry run state, if on dry run mode.
        if self._config.dryrun:
            e1_base_balance = self._config.dryrun_e1_base
            e1_quote_balance = self._config.dryrun_e1_quote
            e2_base_balance = self._config.dryrun_e2_base
            e2_quote_balance = self._config.dryrun_e2_quote
            dry_e1 = DryRunExchange(exchange1, e1_base, e1_quote,
                                    e1_base_balance, e1_quote_balance)
            dry_e2 = DryRunExchange(exchange2, e2_base, e2_quote,
                                    e2_base_balance, e2_quote_balance)
            self.dry_run = DryRun(dry_e1, dry_e2)
            fancy_log(
                "DRY RUN mode initiated. Trades will NOT execute on actual "
                "exchanges.")
        else:
            dry_e1 = None
            dry_e2 = None
            self.dry_run = None


        # Get exchange configuration settings.
        exchange1_configs = {
            "nonce": ccxt.Exchange.milliseconds
        }
        exchange2_configs = {
            "nonce": ccxt.Exchange.milliseconds
        }

        if exchange_key_map:
            exchange1_configs['apiKey'] = (
                exchange_key_map[exchange1][API_KEY])
            exchange1_configs['secret'] = (
                exchange_key_map[exchange1][API_SECRET])
            exchange1_configs['password'] = (
                exchange_key_map[exchange1][PASSWORD])
            exchange2_configs['apiKey'] = (
                exchange_key_map[exchange2][API_KEY])
            exchange2_configs['secret'] = (
                exchange_key_map[exchange2][API_SECRET])
            exchange2_configs['password'] = (
                exchange_key_map[exchange2][PASSWORD])

        self.trader1 = CCXTTrader(
            e1_base,
            e1_quote,
            exchange1,
            num_to_decimal(self._config.slippage),
            exchange1_configs,
            dry_e1)
        self.trader2 = CCXTTrader(
            e2_base,
            e2_quote,
            exchange2,
            num_to_decimal(self._config.slippage),
            exchange2_configs,
            dry_e2)

        # Set to run against test API, if applicable.
        if not self._config.exchange1_test and not self._config.exchange2_test:
            fancy_log("Starting bot against LIVE exchanges.")
            self.is_test_run = False
        elif self._config.exchange1_test and self._config.exchange2_test:
            fancy_log("Starting bot against TEST exchanges.")
            self.trader1.connect_test_api()
            self.trader2.connect_test_api()
            self.is_test_run = True
        else:
            raise AsymmetricTestExchangeConfigError(
                "Only one of the exchanges has been set to a test API.")

        # Load the available markets for the exchange.
        self.trader1.load_markets()
        self.trader2.load_markets()


    def _load_configs(self, config_file_path):
        """Load the configurations of the Autotrageur run.

        Args:
            config_file_path (str): Path to the configuration file used for the
                current autotrageur run.

        Raises:
            IOError: If the encrypted keyfile does not open, and not in
                dryrun mode.
        """
        # Set up the configuration.
        config_map = self.__parse_config_file(config_file_path)
        self._config = Configuration(
            id=str(uuid.uuid4()),
            start_timestamp=int(time.time()),
            **config_map)

    def _setup(self, arguments):
        """Initializes the autotrageur bot for use.

        Setup includes:
        - loading environment variables
        - initializing and connecting to the DB
        - setting up traders to interface with exchange APIs

        Args:
            arguments (dict): Map of the arguments passed to the program.
        """
        # Load environment variables.
        if not self.__load_env_vars():
            raise EnvironmentError('Failed to load all of the necessary'
                                   ' environment variables.')

        # Initialize and connect to the database.
        self.__init_db()

        # Load keyfile.
        exchange_key_map = self.__parse_keyfile(
            arguments[KEYFILE], arguments['--pi_mode'])

        # Set up the Traders for interfacing with exchange APIs.
        self.__setup_traders(exchange_key_map)

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

    @abstractmethod
    def _export_state(self):
        """Exports the state of the autotrageur. Normally exported to a file or
        a database."""
        pass

    @abstractmethod
    def _import_state(self, previous_state, *args):
        """Imports the state of a previous autotrageur run. Normally imported
        from a file or a database.

        Args:
            previous_state (bytes): The previous state of the autotrageur run.
                Expressed as bytes, typically retrieved as a pickled object
                from a database.
        """
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
        # If it's a resumed run, skip loading configuration.
        if arguments['--resume_id']:
            pass
        else:
            if requires_configs:
                self._load_configs(arguments[CONFIGFILE])

        self._setup(arguments)

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
            self._export_state()

            if self._config.dryrun:
                logging.critical("Keyboard Interrupt")
                fancy_log("Summary")
                self.dry_run.log_all()
                fancy_log("End")
            else:
                raise
        except Exception as e:
            self._export_state()

            if not self._config.dryrun:
                logging.critical("Falling back to dry run, error encountered:")
                logging.critical(e)
                self._alert(SUBJECT_LIVE_FAILURE, e)
                self._config.dryrun = True
                self.run_autotrageur(arguments, False)
            else:
                self._alert(SUBJECT_DRY_RUN_FAILURE, e)
                raise
