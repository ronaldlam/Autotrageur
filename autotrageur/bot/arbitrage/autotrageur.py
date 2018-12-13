import getpass
import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

import schedule
import yaml
from dotenv import load_dotenv

import fp_libs.db.maria_db_handler as db_handler
from autotrageur.bot.common.config_constants import DB_NAME, DB_USER
from autotrageur.bot.common.env_var_constants import ENV_VAR_NAMES
from autotrageur.bot.common.notification_constants import (SUBJECT_DRY_RUN_FAILURE,
                                                           SUBJECT_LIVE_FAILURE)
from fp_libs.email_client.simple_email_client import send_all_emails
from fp_libs.logging import bot_logging
from fp_libs.logging.logging_utils import fancy_log
from fp_libs.security.encryption import decrypt
from fp_libs.twilio.twilio_client import TwilioClient
from fp_libs.utilities import keyfile_to_map, to_bytes, to_str
from fp_libs.utils.ccxt_utils import RetryableError, RetryCounter

# Program argument constants.
CONFIGFILE = 'CONFIGFILE'
DBCONFIGFILE = 'DBCONFIGFILE'
KEYFILE = 'KEYFILE'


class AlertError(Exception):
    """Error indicating that one or more methods of communication for `_alert`
    failed."""
    pass


class AutotrageurAuthenticationError(Exception):
    """Incorrect credentials or exchange unavailable when attempting to
    communicate through an exchange's API."""
    pass


class IncompleteArbitrageError(Exception):
    """Error indicating an uneven buy/sell base amount."""
    pass


class IncorrectStateObjectTypeError(Exception):
    """Raised when an incorrect object type is being used as the bot's
    state.  For fcf_autotrageur, FCFCheckpoint is the required object type.
    """
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

    def __init_db(self, db_config_path):
        """Initializes and connects to the database.

        Args:
            db_config_path (str): Path to the database configuration file.
        """
        db_password = getpass.getpass(
            prompt="Enter database password:")

        with open(db_config_path, 'r') as db_file:
            db_info = yaml.safe_load(db_file)

        db_handler.start_db(
            db_info[DB_USER],
            db_password,
            db_info[DB_NAME])
        schedule.every(7).hours.do(db_handler.ping_db)

    def __init_temp_logger(self):
        """Starts the temporary in-memory logger."""
        self.logger = bot_logging.setup_temporary_logger()

    def __init_complete_logger(self):
        """Starts the background logger.

        Note that configs must be loaded.
        """
        if self._config.dryrun and self._config.use_test_api:
            log_dir = 'dryrun-test'
        elif self._config.dryrun:
            log_dir = 'dryrun'
        elif self._config.use_test_api:
            log_dir = 'test'
        else:
            log_dir = 'live'

        self.logger = bot_logging.setup_background_logger(
            self.logger, log_dir, self._config.id)

        # Start listening for logs.
        self.logger.queue_listener.start()

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

    def _load_configs(self, config_file_path):
        """Load the configurations of the Autotrageur run.

        Args:
            config_file_path (str): Path to the configuration file used for the
                current autotrageur run.
        """
        self._config = None

    def _load_twilio(self, twilio_cfg_path):
        """Loads the Twilio configuration file and tests the connection to
        Twilio APIs.

        Args:
            twilio_cfg_path (str): Path to the Twilio configuration file.
        """
        with open(twilio_cfg_path, 'r') as ymlfile:
            self.twilio_config = yaml.safe_load(ymlfile)

        self.twilio_client = TwilioClient(
            os.getenv('ACCOUNT_SID'), os.getenv('AUTH_TOKEN'), self.logger)

        # Make sure there is a valid connection as notifications are a critical
        # service to the bot.
        self.twilio_client.test_connection()

    def _parse_config_file(self, file_name):
        """Parses the given config file into a dict.

        Args:
            file_name (str): The name of the file.

        Returns:
            dict: The configuration file represented as a dict.
        """
        with open(file_name, 'r') as ymlfile:
            return yaml.safe_load(ymlfile)

    def _parse_keyfile(self, keyfile_path, pi_mode=False):
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

    def _send_email(self, subject, msg):
        """Send email alert to preconfigured emails.

        Args:
            subject (str): The subject of the message.
            msg (str): The contents of the email to send out.
        """
        send_all_emails(self._config.email_cfg_path, subject, msg)

    def _setup(self, arguments):
        """Initializes the autotrageur bot for use by setting up core
        components which must be set up before any additional components.

        Core components initialized:
        - logger
        - loading environment variables
        - initializing and connecting to the DB

        * Override this method to set up any additional core components for the
        bot's implementation.

        Args:
            arguments (dict): Map of the arguments passed to the program.
        """
        self.__init_temp_logger()

        # Load environment variables.
        if not self.__load_env_vars():
            raise EnvironmentError('Failed to load all of the necessary'
                                   ' environment variables.')

        # Initialize and connect to the database.
        self.__init_db(arguments[DBCONFIGFILE])

    @abstractmethod
    def _alert(self, subject):
        """Last ditch effort to alert user on operation failure.

        Args:
            subject (str): The subject/topic for the alert.
        """
        pass

    @abstractmethod
    def _clean_up(self):
        """Cleans up the state of the autotrageur."""
        pass

    @abstractmethod
    def _execute_trade(self):
        """Execute the trade, providing necessary failsafes."""
        pass

    @abstractmethod
    def _export_state(self):
        """Exports the state of the autotrageur. Normally exported to a file or
        a database."""
        pass

    @abstractmethod
    def _final_log(self):
        """Outputs a final log and/or console output during teardown of the
        bot."""
        pass

    @abstractmethod
    def _import_state(self, *args):
        """Imports the state of a previous autotrageur run. Normally imported
        from a file or a database.

        Args:
            *args: Arbitrary amount of arguments representing objects required
                to retrieve previous state.
        """
        pass

    @abstractmethod
    def _poll_opportunity(self):
        """Poll exchanges for arbitrage opportunity.

        Returns:
            bool: Whether there is an opportunity.
        """
        pass

    def _post_setup(self, arguments):
        """Initializes any additional components which rely on the core
        components.

        Components initialized:
        - Logger (completes background logger setup)

        Args:
            arguments (dict): Map of the arguments passed to the program.
        """
        self.__init_complete_logger()

    def _wait(self):
        """Wait for the specified polling interval."""
        time.sleep(self._config.poll_wait_default)

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
        # If not resuming a run, must load configs first.
        if requires_configs and not arguments['--resume_id']:
            self._load_configs(arguments[CONFIGFILE])

        # Initialize core components of the bot.
        self._setup(arguments)

        # Set up the rest of the bot.
        self._post_setup(arguments)

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
            if self._config.dryrun:
                logging.critical("Keyboard Interrupt")
            else:
                raise
        except Exception as e:
            if not self._config.dryrun:
                logging.critical(e)
                self._alert(SUBJECT_LIVE_FAILURE)
                raise
            else:
                self._alert(SUBJECT_DRY_RUN_FAILURE)
                raise
        finally:
            self._export_state()
            fancy_log("Summary")
            self._final_log()
            fancy_log("End")
