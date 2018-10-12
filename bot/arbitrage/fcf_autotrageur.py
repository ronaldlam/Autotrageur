import copyreg
import logging
import os
import pickle
import pprint
import time
import traceback
import uuid

import schedule
import yaml

import bot.arbitrage.arbseeker as arbseeker
import libs.db.maria_db_handler as db_handler
from bot.arbitrage.autotrageur import Autotrageur
from bot.arbitrage.fcf.balance_checker import FCFBalanceChecker
from bot.arbitrage.fcf.fcf_checkpoint import FCFCheckpoint
from bot.arbitrage.fcf.fcf_checkpoint_utils import pickle_fcf_checkpoint
from bot.arbitrage.fcf.strategy import FCFStrategyBuilder
from bot.common.config_constants import (TWILIO_RECIPIENT_NUMBERS,
                                         TWILIO_SENDER_NUMBER)
from bot.common.db_constants import (FCF_AUTOTRAGEUR_CONFIG_COLUMNS,
                                     FCF_AUTOTRAGEUR_CONFIG_PRIM_KEY_ID,
                                     FCF_AUTOTRAGEUR_CONFIG_PRIM_KEY_START_TS,
                                     FCF_AUTOTRAGEUR_CONFIG_TABLE,
                                     FCF_STATE_PRIM_KEY_ID, FCF_STATE_TABLE,
                                     FOREX_RATE_PRIM_KEY_ID, FOREX_RATE_TABLE,
                                     TRADE_OPPORTUNITY_PRIM_KEY_ID,
                                     TRADE_OPPORTUNITY_TABLE,
                                     TRADES_PRIM_KEY_SIDE,
                                     TRADES_PRIM_KEY_TRADE_OPP_ID,
                                     TRADES_TABLE)
from libs.constants.decimal_constants import TEN, ZERO
from libs.db.maria_db_handler import InsertRowObject
from libs.email_client.simple_email_client import send_all_emails
from libs.fiat_symbols import FIAT_SYMBOLS
from libs.twilio.twilio_client import TwilioClient
from libs.utilities import num_to_decimal


class FCFAlertError(Exception):
    """Error indicating that one or more methods of communication for `_alert`
    failed."""
    pass


class IncompleteArbitrageError(Exception):
    """Error indicating an uneven buy/sell base amount."""
    pass


class InsufficientCryptoBalance(Exception):
    """Thrown when there is not enough crypto balance to fulfill the matching
    sell order."""
    pass


class IncorrectStateObjectTypeError(Exception):
    """Raised when an incorrect object type is being used as the bot's
    state.  For fcf_autotrageur, FCFCheckpoint is the required object type.
    """
    pass


class FCFAutotrageur(Autotrageur):
    """The fiat-crypto-fiat Autotrageur.

    This implementation of the Autotrageur polls two specified fiat to
    crypto markets. Given the target high and low spreads between the
    fiat currencies, this algorithm will execute a trade in the
    direction of exchange two (buy crypto on exchange one, sell crypto
    on exchange two) if the calculated spread is greater than the
    specified target high; vice versa if the calculated spread is less
    than the specified target low.
    """
    def __init__(self, logger):
        """Constructor."""
        self.logger = logger

    def __load_twilio(self, twilio_cfg_path):
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

    def __persist_config(self):
        """Persists the configuration for this `fcf_autotrageur` run."""
        fcf_autotrageur_config_row = db_handler.build_row(
            FCF_AUTOTRAGEUR_CONFIG_COLUMNS, self._config._asdict())
        config_row_obj = InsertRowObject(
            FCF_AUTOTRAGEUR_CONFIG_TABLE,
            fcf_autotrageur_config_row,
            (FCF_AUTOTRAGEUR_CONFIG_PRIM_KEY_ID,
            FCF_AUTOTRAGEUR_CONFIG_PRIM_KEY_START_TS))

        db_handler.insert_row(config_row_obj)
        db_handler.commit_all()

    def __persist_forex(self, trader):
        """Persists the current forex data.

        NOTE: The trader's forex_id is updated here and is cached until
        the next update.

        Args:
            trader (CCXTTrader): The CCXTTrader to use.
        """
        trader.forex_id = str(uuid.uuid4())
        row_data = {
            'id': trader.forex_id,
            'quote': trader.quote,
            'rate': trader.forex_ratio,
            'local_timestamp': int(time.time())
        }
        forex_row_obj = InsertRowObject(
            FOREX_RATE_TABLE,
            row_data,
            (FOREX_RATE_PRIM_KEY_ID,))
        db_handler.insert_row(forex_row_obj)
        db_handler.commit_all()

    def __update_forex(self, trader):
        """Update the internally stored forex ratio and store in db.

        Args:
            trader (CCXTTrader): The CCXTTrader to use.
        """
        trader.set_forex_ratio()
        self.__persist_forex(trader)

    def __persist_trade_data(self, buy_response, sell_response, trade_metadata):
        """Persists data regarding the current trade into the database.

        If a trade has been executed, we add any necessary information (such as
        foreign key IDs) to the trade responses before saving to the database.

        Args:
            buy_response (dict): The autotrageur unified response from the
                executed buy trade.  If a buy trade was unsuccessful, then
                buy_response is None.
            sell_response (dict): The autotrageur unified response from the
                executed sell trade.  If a sell trade was unsuccessful, then
                sell_response is None.
            trade_metadata (TradeMetadata): The trade metadata prepared by the
                autotrageur strategy.
        """
        # Persist the spread_opp.
        trade_opportunity_id = trade_metadata.spread_opp.id
        spread_opp = trade_metadata.spread_opp._asdict()
        trade_opp_row_obj = InsertRowObject(
            TRADE_OPPORTUNITY_TABLE,
            spread_opp,
            (TRADE_OPPORTUNITY_PRIM_KEY_ID, ))
        db_handler.insert_row(trade_opp_row_obj)

        # Persist the executed buy order, if available.
        if buy_response is not None:
            buy_response['trade_opportunity_id'] = trade_opportunity_id
            buy_response['autotrageur_config_id'] = self._config.id
            buy_response['autotrageur_config_start_timestamp'] = (
                self._config.start_timestamp)
            buy_trade_row_obj = InsertRowObject(
                TRADES_TABLE,
                buy_response,
                (TRADES_PRIM_KEY_TRADE_OPP_ID, TRADES_PRIM_KEY_SIDE))
            db_handler.insert_row(buy_trade_row_obj)

        # Persist the executed sell order, if available.
        if sell_response is not None:
            sell_response['trade_opportunity_id'] = trade_opportunity_id
            sell_response['autotrageur_config_id'] = self._config.id
            sell_response['autotrageur_config_start_timestamp'] = (
                self._config.start_timestamp)
            sell_trade_row_obj = InsertRowObject(
                TRADES_TABLE,
                sell_response,
                (TRADES_PRIM_KEY_TRADE_OPP_ID, TRADES_PRIM_KEY_SIDE))
            db_handler.insert_row(sell_trade_row_obj)

        db_handler.commit_all()

    def __construct_strategy(self):
        """Initializes the Algorithm component."""
        strategy_builder = FCFStrategyBuilder()
        return (strategy_builder
            .set_has_started(False)
            .set_h_to_e1_max(num_to_decimal(self._config.h_to_e1_max))
            .set_h_to_e2_max(num_to_decimal(self._config.h_to_e2_max))
            .set_max_trade_size(num_to_decimal(self._config.max_trade_size))
            .set_spread_min(num_to_decimal(self._config.spread_min))
            .set_vol_min(num_to_decimal(self._config.vol_min))
            .set_manager(self)
            .build()
        )

    def __setup_forex(self):
        """Sets up any forex services for fiat conversion, if necessary."""
        # Bot considers stablecoin (USDT - Tether) prices as roughly equivalent
        # to USD fiat.
        for trader in (self.trader1, self.trader2):
            if ((trader.quote in FIAT_SYMBOLS)
                    and (trader.quote != 'USD')
                    and (trader.quote != 'USDT')):
                logging.info("Set fiat conversion to USD as necessary for: {}"
                             " with quote: {}".format(trader.exchange_name,
                                                      trader.quote))
                trader.conversion_needed = True
                self.__update_forex(trader)
                # TODO: Adjust interval once real-time forex implemented.
                schedule.every().hour.do(self.__update_forex, trader)

    def __verify_sold_amount(
            self, bought_amount, sell_trader, buy_response, sell_response):
        """Ensure that the sold amount is within tolerance.

        Args:
            bought_amount (Decimal): The base amount bought.
            sell_trader (CCXTTrader): The sell side trader.
            buy_response (dict): The buy response.
            sell_response (dict): The sell response.

        Raises:
            IncompleteArbitrageError: If the sold amount is not within
                the prescribed tolerance.
        """
        rounded_sell_amount = sell_trader.round_exchange_precision(
            bought_amount)
        amount_precision = sell_trader.get_amount_precision()
        difference = rounded_sell_amount - sell_response['pre_fee_base']

        if amount_precision is None:
            # Exchange has arbitrary precision.
            tolerance = ZERO
        else:
            tolerance = TEN ** num_to_decimal(-amount_precision)

        if abs(difference) > tolerance:
            msg = ("The purchased base amount does not match with "
                    "the sold amount. Normal execution has "
                    "terminated.\nBought amount: {}\n, Expected "
                    "sell amount: {}\nSold amount:"
                    " {}\n\nBuy results:\n\n{}\n\nSell results:\n\n"
                    "{}\n").format(
                bought_amount,
                rounded_sell_amount,
                sell_response['pre_fee_base'],
                pprint.pformat(buy_response),
                pprint.pformat(sell_response))

            raise IncompleteArbitrageError(msg)

    # @Override
    def _alert(self, subject):
        """Last ditch effort to alert user on operation failure.

        Args:
            subject (str): The subject/topic for the alert.
        """
        alert_error = False
        try:
            self._send_email(subject, traceback.format_exc())
        except Exception as exc:
            alert_error = True
            logging.debug("An error occurred trying to send an email.")
            logging.error(exc, exc_info=True)
        finally:
            try:
                self.twilio_client.phone(
                    [subject, traceback.format_exc()],
                    self.twilio_config[TWILIO_RECIPIENT_NUMBERS],
                    self.twilio_config[TWILIO_SENDER_NUMBER],
                    is_mock_call=self._config.dryrun or self.is_test_run)
            except Exception as exc:
                alert_error = True
                logging.debug("An error occurred trying to phone with twilio.")
                logging.error(exc, exc_info=True)

        if alert_error:
            raise FCFAlertError("One or more methods of communication have"
                " failed.  Check the logs for more detail.")

    # @Override
    def _clean_up(self):
        """Cleans up the state of the autotrageur before performing next
        actions which may be harmed by previous state."""
        self._strategy.clean_up()

    # @Override
    def _execute_trade(self):
        """Execute the arbitrage."""
        buy_response = None
        sell_response = None
        trade_metadata = self._strategy.get_trade_data()

        if self._config.dryrun:
            logging.debug("**Dry run - begin fake execution")
            buy_response = arbseeker.execute_buy(
                trade_metadata.buy_trader,
                trade_metadata.buy_price)

            executed_amount = buy_response['post_fee_base']
            sell_response = arbseeker.execute_sell(
                trade_metadata.sell_trader,
                trade_metadata.sell_price,
                executed_amount)
            self._strategy.finalize_trade(buy_response, sell_response)
            self._dry_run_manager.log_balances()
            self.__persist_trade_data(
                buy_response, sell_response, trade_metadata)
            logging.debug("**Dry run - end fake execution")
        else:
            try:
                buy_response = arbseeker.execute_buy(
                    trade_metadata.buy_trader,
                    trade_metadata.buy_price)
                bought_amount = buy_response['post_fee_base']
            except Exception as exc:
                self._send_email("BUY ERROR ALERT - CONTINUING", repr(exc))
                logging.error(exc, exc_info=True)
                self._strategy.strategy_state = self.checkpoint.strategy_state
            else:
                # If an exception is thrown, we want the program to stop on the
                # second trade.
                try:
                    sell_response = arbseeker.execute_sell(
                        trade_metadata.sell_trader,
                        trade_metadata.sell_price,
                        bought_amount)
                    self.__verify_sold_amount(
                        bought_amount,
                        trade_metadata.sell_trader,
                        buy_response,
                        sell_response)
                except Exception as exc:
                    self._send_email("SELL ERROR ALERT - ABORT", repr(exc))
                    logging.error(exc, exc_info=True)
                    raise
                else:
                    self._strategy.finalize_trade(buy_response, sell_response)
                    self._send_email(
                        "TRADE SUMMARY",
                        "Buy results:\n\n{}\n\nSell results:\n\n{}\n".format(
                            pprint.pformat(buy_response),
                            pprint.pformat(sell_response)))
            finally:
                self.__persist_trade_data(
                    buy_response, sell_response, trade_metadata)

    # @Override
    def _export_state(self):
        """Exports the state of the autotrageur to a database."""
        logging.debug("#### Exporting bot's current state")

        # Set the dry run state, if in dry run mode.
        if self._config.dryrun:
            self.checkpoint.dry_run_manager = self._dry_run_manager

        # Register copyreg.pickle with Checkpoint object and helper function
        # for better backwards-compatibility in pickling.
        # (See 'fcf_checkpoint_utils' module for more details)
        copyreg.pickle(FCFCheckpoint, pickle_fcf_checkpoint)

        # The generated ID can be used as the `resume_id` to resume the bot
        # from the saved state.
        fcf_state_map = {
            'id': str(uuid.uuid4()),
            'autotrageur_config_id': self._config.id,
            'autotrageur_config_start_timestamp': self._config.start_timestamp,
            'state': pickle.dumps(self.checkpoint)
        }
        logging.debug(
            "#### The exported checkpoint object is: {0!r}".format(
                self.checkpoint))
        logging.info("Exported with resume id: {}".format(
            fcf_state_map[FCF_STATE_PRIM_KEY_ID]))
        fcf_state_row_obj = InsertRowObject(
            FCF_STATE_TABLE,
            fcf_state_map,
            (FCF_STATE_PRIM_KEY_ID,))
        db_handler.insert_row(fcf_state_row_obj)
        db_handler.commit_all()

    # @Override
    def _import_state(self, resume_id):
        """Imports the state of a previous autotrageur run.

        Sets the FCFCheckpoint to be a snapshot of the previous autotrageur's
        state.

        Args:
            resume_id (str): The unique ID used to resume the bot from a
                previous run.
        """
        logging.debug("#### Importing bot's previous state")
        raw_result = db_handler.execute_parametrized_query(
                "SELECT state FROM fcf_state where id = %s;",
                (resume_id,))

        # The raw result comes back as a list of tuples.  We expect only
        # one result as the `autotrageur_resume_id` is unique per
        # export.
        previous_checkpoint = pickle.loads(raw_result[0][0])

        if not isinstance(previous_checkpoint, FCFCheckpoint):
            raise IncorrectStateObjectTypeError(
                "FCFCheckpoint is the required type.  {} type was given."
                    .format(type(previous_checkpoint)))

        self.checkpoint = previous_checkpoint

    # @Override
    def _poll_opportunity(self):
        """Poll exchanges for arbitrage opportunity.

        Returns:
            bool: Whether there is an opportunity.
        """
        return self._strategy.poll_opportunity()

    # @Override
    def _post_setup(self, arguments):
        """Initializes any additional components which rely on the core
        components.

        Components initialized:
        - Twilio Client
        - Forex Client
        - BalanceChecker

        Other responsibilities:
        - Persists Configuration and Forex in the database.

        Args:
            arguments (dict): Map of the arguments passed to the program.
        """
        super()._post_setup(arguments)

        # Set up Twilio Client.
        self.__load_twilio(self._config.twilio_cfg_path)

        # Set up Forex client.
        self.__setup_forex()

        # Persist the configuration.
        self.__persist_config()

        # Initialize a Balance Checker.
        self.balance_checker = FCFBalanceChecker(
            self.trader1, self.trader2, self._send_email)

    def _send_email(self, subject, msg):
        """Send email alert to preconfigured emails.

        Args:
            subject (str): The subject of the message.
            msg (str): The contents of the email to send out.
        """
        send_all_emails(self._config.email_cfg_path, subject, msg)

    # @Override
    def _setup(self, arguments):
        """Initializes the autotrageur bot for use by setting up core
        components which must be set up before any additional components.

        In addition to superclass setup, the following core components are
        initialized:
        - Checkpoint (for state-related variables)
        - Algorithm
        - Dry Run (on resume)

        If starting from resume:
          - Import the previous Checkpoint, setting a checkpoint object.
          - Restore any state from the Checkpoint
        Else:
          - Initialize the Checkpoint object with the Configuration
          - Initialize the Algorithm

        Args:
            arguments (dict): Map of the arguments passed to the program.
        """
        super()._setup(arguments)

        resume_id = arguments['--resume_id']
        if resume_id:
            self._import_state(resume_id)
            self._config = self.checkpoint.config
            self._strategy = self.__construct_strategy()
            self.checkpoint.restore_strategy(self._strategy)
            self._dry_run_manager = self.checkpoint.dry_run_manager
            logging.debug(
                '#### Restored State objects: {0!r}\n{1!r}\n{2!r}'.format(
                    self._config,
                    self._strategy.state,
                    self._dry_run_manager))
        else:
            # Initialize a Checkpoint object to hold state.
            self.checkpoint = FCFCheckpoint(self._config)

            # Set up the Algorithm.
            self._strategy = self.__construct_strategy()

    # @Override
    def _wait(self):
        """Wait for the specified polling interval.

        We use the Autotrageur default unless a chunked trade is in
        progress.
        """
        if self._strategy.trade_chunker.trade_completed:
            super()._wait()
        else:
            time.sleep(self._config.poll_wait_short)
