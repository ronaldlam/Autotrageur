import getpass
import logging
import os
import time
import uuid
from abc import ABC, abstractmethod
from collections import namedtuple
from pathlib import Path

import schedule
import yaml
from dotenv import load_dotenv

import fp_libs.db.maria_db_handler as db_handler
from autotrageur.bot.common.config_constants import DB_NAME, DB_USER
from autotrageur.bot.common.env_var_constants import ENV_VAR_NAMES
from autotrageur.bot.common.notification_constants import (SUBJECT_DRY_RUN_FAILURE,
                                                           SUBJECT_LIVE_FAILURE)
from fp_libs.logging import bot_logging
from fp_libs.logging.logging_utils import fancy_log
from fp_libs.utils.ccxt_utils import RetryableError, RetryCounter

# Program argument constants.
CONFIGFILE = 'CONFIGFILE'
DBCONFIGFILE = 'DBCONFIGFILE'
KEYFILE = 'KEYFILE'


class Configuration(namedtuple('Configuration', [
        'dryrun', 'dryrun_e1_base', 'dryrun_e1_quote',
        'dryrun_e2_base', 'dryrun_e2_quote', 'email_cfg_path', 'exchange1',
        'exchange1_pair', 'exchange2', 'exchange2_pair', 'use_test_api',
        'h_to_e1_max', 'h_to_e2_max', 'id', 'max_trade_size',
        'poll_wait_default', 'poll_wait_short', 'slippage', 'spread_min',
        'start_timestamp', 'twilio_cfg_path', 'vol_min'])):
    """Holds all of the configuration for the autotrageur bot.

    Args:
        dryrun (bool): If True, this bot's run is considered to be a dry run
            against fake exchange objects and no real trades are performed.
        dryrun_e1_base (str): In dry run, the base used for exchange one.
        dryrun_e1_quote (str): In dry run, the quote used for exchange one.
        dryrun_e2_base (str): In dry run, the base used for exchange two.
        dryrun_e2_quote (str): In dry run, the quote used for exchange two.
        email_cfg_path (str): Path to the email config file, used for sending
            notifications.
        exchange1 (str): Name of exchange one.
        exchange1_pair (str): Symbol of the pair to use for exchange one.
        exchange2 (str): Name of the exchange two.
        exchange2_pair (str): Symbol of the pair to use for exchange two.
        use_test_api (bool): If True, will use the test APIs for both
            exchanges.
        h_to_e1_max (float): The historical max spread going to exchange one.
        h_to_e2_max (float): The historical max spread going to exchange two.
        id (str): The unique id tagged to the current configuration and bot
            run.  This is not provided from the config file and set during
            initialization.
        max_trade_size (float): The maximum USD value of any given trade.
        poll_wait_default (int): Default waiting time (in seconds) in between
            polls.
        poll_wait_short (int): The shortened poll waiting time (in seconds),
            used when trade is chunked and in progress.
        slippage (float): Percentage downside of limit order slippage tolerable
            for market order emulations.
        spread_min (float): The minimum spread increment for considering trade
            targets.
        start_timestamp (float): The unix timestamp tagged against the current
            bot run.  This is not provided from the config file and set during
            initialization.
        twilio_cfg_path (str): Path for the twilio config file, used for
            sending notifications.
        vol_min (float): The minimum volume trade in USD.
    """
    __slots__ = ()


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
        """Parses the given config file into a dict.

        Args:
            file_name (str): The name of the file.

        Returns:
            dict: The configuration file represented as a dict.
        """
        with open(file_name, 'r') as ymlfile:
            return yaml.safe_load(ymlfile)

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
        # Set up the configuration.
        config_map = self.__parse_config_file(config_file_path)
        self._config = Configuration(
            id=str(uuid.uuid4()),
            start_timestamp=int(time.time()),
            **config_map)

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
                logging.critical("Falling back to dry run, error encountered:")
                logging.critical(e)
                self._alert(SUBJECT_LIVE_FAILURE)
                self._config.dryrun = True
                self.run_autotrageur(arguments, False)
            else:
                self._alert(SUBJECT_DRY_RUN_FAILURE)
                raise
        finally:
            self._export_state()
            self._final_log()
            fancy_log("Summary")
            fancy_log("End")
