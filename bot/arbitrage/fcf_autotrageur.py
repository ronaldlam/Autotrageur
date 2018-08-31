import logging
import os
import pickle
import pprint
import time
import traceback
import uuid

import ccxt
import schedule
import yaml

import bot.arbitrage.arbseeker as arbseeker
import libs.db.maria_db_handler as db_handler
from bot.arbitrage.autotrageur import Autotrageur
from bot.arbitrage.fcf.balance_checker import FCFBalanceChecker
from bot.arbitrage.fcf.checkpoint import FCFCheckpoint
from bot.arbitrage.fcf.strategy import FCFStrategyBuilder
from bot.common.config_constants import (DRYRUN, EMAIL_CFG_PATH, H_TO_E1_MAX,
                                         H_TO_E2_MAX, ID, MAX_TRADE_SIZE,
                                         SPREAD_MIN, START_TIMESTAMP,
                                         TWILIO_CFG_PATH,
                                         TWILIO_RECIPIENT_NUMBERS,
                                         TWILIO_SENDER_NUMBER, VOL_MIN)
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
from libs.db.maria_db_handler import InsertRowObject
from libs.email_client.simple_email_client import send_all_emails
from libs.fiat_symbols import FIAT_SYMBOLS
from libs.twilio.twilio_client import TwilioClient
from libs.utilities import num_to_decimal


class FCFAuthenticationError(Exception):
    """Incorrect credentials or exchange unavailable when attempting to
    communicate through an exchange's API."""
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
            FCF_AUTOTRAGEUR_CONFIG_COLUMNS, self.config)
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
            buy_response['autotrageur_config_id'] = self.config[ID]
            buy_response['autotrageur_config_start_timestamp'] = (
                self.config[START_TIMESTAMP])
            buy_trade_row_obj = InsertRowObject(
                TRADES_TABLE,
                buy_response,
                (TRADES_PRIM_KEY_TRADE_OPP_ID, TRADES_PRIM_KEY_SIDE))
            db_handler.insert_row(buy_trade_row_obj)

        # Persist the executed sell order, if available.
        if sell_response is not None:
            sell_response['trade_opportunity_id'] = trade_opportunity_id
            sell_response['autotrageur_config_id'] = self.config[ID]
            sell_response['autotrageur_config_start_timestamp'] = (
                self.config[START_TIMESTAMP])
            sell_trade_row_obj = InsertRowObject(
                TRADES_TABLE,
                sell_response,
                (TRADES_PRIM_KEY_TRADE_OPP_ID, TRADES_PRIM_KEY_SIDE))
            db_handler.insert_row(sell_trade_row_obj)

        db_handler.commit_all()

    def __construct_strategy(self, resume_id=None):
        """Sets up the algorithm by either initializing or restoring the
        algorithm's state.

        Args:
            resume_id (str): The configuration id which links to the
                autotrageur's previous state.  Defaults to None, in the case
                that this run is new.
        """
        strategy_builder = FCFStrategyBuilder()
        (strategy_builder
            .set_has_started(False)
            .set_h_to_e1_max(num_to_decimal(self.config[H_TO_E1_MAX]))
            .set_h_to_e2_max(num_to_decimal(self.config[H_TO_E2_MAX]))
            .set_max_trade_size(num_to_decimal(self.config[MAX_TRADE_SIZE]))
            .set_spread_min(num_to_decimal(self.config[SPREAD_MIN]))
            .set_vol_min(num_to_decimal(self.config[VOL_MIN]))
            .set_checkpoint(FCFCheckpoint(self.config[ID]))
            .set_trader1(self.trader1)
            .set_trader2(self.trader2))

        # Setup and fetch the wallet balances available for each trader.
        self.__setup_wallet_balances(strategy_builder)

        if resume_id:
            logging.debug("#### resume_id: {}".format(resume_id))
            raw_result = db_handler.execute_parametrized_query(
                "SELECT state FROM fcf_state where id = %s;",
                (resume_id,))

            # The raw result comes back as a list of tuples.  We expect only
            # one result as the `autotrageur_resume_id` is unique per
            # export.
            self._import_state(raw_result[0][0], strategy_builder)
            strategy = strategy_builder.build()

            # Overwrite state set in config.
            strategy.restore()
        else:
            strategy = strategy_builder.build()

        return strategy

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

    def __setup_wallet_balances(self, strategy_builder):
        """Sets up the balances for each exchange, on each trader.

        Also sets up the FCFBalanceChecker to monitor wallet balances for the
        algorithm.

        Args:
            strategy_builder (FCFStrategyBuilder): The builder object to
                construct the FCFStrategy.
        """
        try:
            # Dry run uses balances set in the configuration files.
            self.trader1.update_wallet_balances()
            self.trader2.update_wallet_balances()
        except (ccxt.AuthenticationError, ccxt.ExchangeNotAvailable) as auth_error:
            logging.error(auth_error)
            raise FCFAuthenticationError(auth_error)

        strategy_builder.set_balance_checker(
            FCFBalanceChecker(self.trader1, self.trader2, self._send_email))

    def _alert(self, subject, exception):
        """Last ditch effort to alert user on operation failure.

        Args:
            subject (str): The subject/topic for the alert.
            exception (Exception): The exception to alert about.
        """
        self._send_email(subject, traceback.format_exc())
        self.twilio_client.phone(
            [subject, traceback.format_exc()],
            self.twilio_config[TWILIO_RECIPIENT_NUMBERS],
            self.twilio_config[TWILIO_SENDER_NUMBER],
            is_mock_call=self.config[DRYRUN] or self.is_test_run)

    def _clean_up(self):
        """Cleans up the state of the autotrageur before performing next
        actions which may be harmed by previous state."""
        self.strategy.clean_up()

    def _execute_trade(self):
        """Execute the arbitrage."""
        buy_response = None
        sell_response = None
        trade_metadata = self.strategy.get_trade_data()

        if self.config[DRYRUN]:
            logging.debug("**Dry run - begin fake execution")
            buy_response = arbseeker.execute_buy(
                trade_metadata.buy_trader,
                trade_metadata.buy_price)

            executed_amount = buy_response['post_fee_base']
            sell_response = arbseeker.execute_sell(
                trade_metadata.sell_trader,
                trade_metadata.sell_price,
                executed_amount)
            self.strategy.finalize_trade(buy_response, sell_response)
            self.dry_run.log_balances()
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
                self.strategy.restore()
            else:
                # If an exception is thrown, we want the program to stop on the
                # second trade.
                try:
                    sell_response = arbseeker.execute_sell(
                        trade_metadata.sell_trader,
                        trade_metadata.sell_price,
                        bought_amount)

                    sell_trader = trade_metadata.sell_trader
                    rounded_sell_amount = sell_trader.round_exchange_precision(
                        bought_amount)

                    if rounded_sell_amount != sell_response['pre_fee_base']:
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
                except Exception as exc:
                    self._send_email("SELL ERROR ALERT - ABORT", repr(exc))
                    logging.error(exc, exc_info=True)
                    raise
                else:
                    self.strategy.finalize_trade(buy_response, sell_response)
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

        # The generated ID can be used as the `resume_id` to resume the bot
        # from the saved state.
        fcf_state_map = {
            'id': str(uuid.uuid4()),
            'autotrageur_config_id': self.config[ID],
            'autotrageur_config_start_timestamp': self.config[START_TIMESTAMP],
            'state': pickle.dumps(self.strategy.checkpoint)
        }
        logging.debug("#### The exported checkpoint object __dict__ is: {}"
                      .format(pprint.pformat(self.strategy.checkpoint.__dict__)))
        fcf_state_row_obj = InsertRowObject(
            FCF_STATE_TABLE,
            fcf_state_map,
            (FCF_STATE_PRIM_KEY_ID,))
        db_handler.insert_row(fcf_state_row_obj)
        db_handler.commit_all()

    # @Override
    def _import_state(self, previous_state, strategy_builder):
        """Imports the state of a previous autotrageur run.

        Args:
            previous_state (bytes): The previous state of the autotrageur run.
                Expressed as bytes, typically pickled into a database.
            strategy_builder (FCFStrategyBuilder): The builder object to
                construct the FCFStrategy.
        """
        logging.debug("#### Importing bot's previous state")
        checkpoint = pickle.loads(previous_state)

        if not isinstance(checkpoint, FCFCheckpoint):
            raise IncorrectStateObjectTypeError(
                "FCFCheckpoint is the required type.  {} type was given."
                    .format(type(checkpoint)))

        logging.debug("#### The restored checkpoint object __dict__ is now: {}"
            .format(pprint.pformat(checkpoint.__dict__)))
        strategy_builder.set_checkpoint(checkpoint)

    # @Override
    def _load_configs(self, arguments):
        """Load the configurations of the Autotrageur run.

        Args:
            arguments (dict): Map of the arguments passed to the program.

        Raises:
            IOError: If the encrypted keyfile does not open, and not in
                dryrun mode.
        """
        super()._load_configs(arguments)

        # Load the twilio config file, and test the twilio credentials.
        self.__load_twilio(self.config[TWILIO_CFG_PATH])

    def _poll_opportunity(self):
        """Poll exchanges for arbitrage opportunity.

        Returns:
            bool: Whether there is an opportunity.
        """
        return self.strategy.poll_opportunity()

    def _send_email(self, subject, msg):
        """Send email alert to preconfigured emails.

        Args:
            subject (str): The subject of the message.
            msg (str): The contents of the email to send out.
        """
        send_all_emails(self.config[EMAIL_CFG_PATH], subject, msg)

    # @Override
    def _setup(self, resume_id=None):
        """Initializes the autotrageur bot for use.

        Sets up the algorithm by either initializing or restoring the
        algorithm's state.

        Other responsibilities include:
        - Initializing forex services and state for the bot.
        - Persisting configurations and forex ratio in the database.

        Args:
            resume_id (str): The unique id which links to the autotrageur's
                previous state.  Defaults to None, in the case that this run is
                new.

        Raises:
            FCFAuthenticationError: If not dryrun and authentication fails.
        """
        super()._setup()

        # Set the configuration start_timestamp and id.  This is used as the
        # compound primary key for the current bot run.
        self.config[START_TIMESTAMP] = int(time.time())
        self.config[ID] = str(uuid.uuid4())

        # Set up the algorithm.
        self.strategy = self.__construct_strategy(resume_id)
        self.__persist_config()

        # Set up forex service.
        self.__setup_forex()

    # @Override
    def _wait(self):
        if self.strategy.trade_chunker.trade_completed:
            super()._wait()
        else:
            time.sleep(2)