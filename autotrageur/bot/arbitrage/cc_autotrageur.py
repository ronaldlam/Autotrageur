import copyreg
import logging
import pickle
import pprint
import time
import traceback
import uuid
from collections import namedtuple

import ccxt

import autotrageur.bot.arbitrage.arbseeker as arbseeker
import fp_libs.db.maria_db_handler as db_handler
from autotrageur.bot.arbitrage.autotrageur import (AlertError, Autotrageur,
                                                   AutotrageurAuthenticationError,
                                                   IncompleteArbitrageError,
                                                   IncorrectStateObjectTypeError)
from autotrageur.bot.arbitrage.cc.checkpoint import CCCheckpoint
from autotrageur.bot.arbitrage.cc.checkpoint_utils import pickle_cc_checkpoint
from autotrageur.bot.arbitrage.cc.stat_tracker import CCStatTracker
from autotrageur.bot.arbitrage.cc.strategy import CCStrategyBuilder
from autotrageur.bot.common.config_constants import (TWILIO_RECIPIENT_NUMBERS,
                                                     TWILIO_SENDER_NUMBER)
from autotrageur.bot.common.db_constants import (CC_AUTOTRAGEUR_CONFIG_COLUMNS,
                                                 CC_AUTOTRAGEUR_CONFIG_PRIM_KEY_ID,
                                                 CC_AUTOTRAGEUR_CONFIG_TABLE,
                                                 CC_MEASURES_PRIM_KEY_ID,
                                                 CC_MEASURES_TABLE,
                                                 CC_SESSION_PRIM_KEY_ID,
                                                 CC_SESSION_TABLE,
                                                 CC_STATE_PRIM_KEY_ID,
                                                 CC_STATE_TABLE,
                                                 TRADE_OPPORTUNITY_PRIM_KEY_ID,
                                                 TRADE_OPPORTUNITY_TABLE,
                                                 TRADES_PRIM_KEY_SIDE,
                                                 TRADES_PRIM_KEY_TRADE_OPP_ID,
                                                 TRADES_TABLE)
from autotrageur.bot.trader.ccxt_trader import CCXTTrader
from autotrageur.bot.trader.dry_run import DryRunExchange
from fp_libs.constants.ccxt_constants import API_KEY, API_SECRET, PASSWORD
from fp_libs.constants.decimal_constants import TEN, ZERO
from fp_libs.db.maria_db_handler import InsertRowObject
from fp_libs.logging.logging_utils import fancy_log
from fp_libs.utilities import num_to_decimal, split_symbol

# Default error message for phone call.
DEFAULT_PHONE_MESSAGE = "Please check logs and e-mail for full stack trace."


class CCSession(namedtuple('CCSession', [
        'id', 'autotrageur_config_id', 'start_timestamp', 'stop_timestamp'])):
    """Holds descriptors for a session of an CCAutotrageur bot.

    Args:
        id (str): The unique uuid.
        autotrageur_config_id (str): The unique uuid of the config.
        start_timestamp (int): The start unix timestamp.
        stop_timestamp (int): The stop unix timestamp.
    """
    __slots__ = ()


class CCAutotrageur(Autotrageur):
    """The crypto-crypto Autotrageur.

    This implementation of the Autotrageur polls two specified crypto to
    crypto markets. Given a profitable target spread, the bot will make
    a pair maximum sized trades and try to rebalance the setup through
    withdrawls.
    """
    def __construct_strategy(self):
        """Initializes the Algorithm component.

        Returns:
            CCStrategy: The strategy object.
        """
        strategy_builder = CCStrategyBuilder()
        return (strategy_builder
            .set_max_trade_size(num_to_decimal(self._config.max_trade_size))
            .set_spread_min(num_to_decimal(self._config.spread_min))
            .set_manager(self)
                .build())

    def __persist_config(self):
        """Persists the configuration for this `cc_autotrageur` run."""
        cc_autotrageur_config_row = db_handler.build_row(
            CC_AUTOTRAGEUR_CONFIG_COLUMNS, self._config._asdict())
        config_row_obj = InsertRowObject(
            CC_AUTOTRAGEUR_CONFIG_TABLE,
            cc_autotrageur_config_row,
            (CC_AUTOTRAGEUR_CONFIG_PRIM_KEY_ID,))

        db_handler.insert_row(config_row_obj)
        db_handler.commit_all()

    def __persist_session(self):
        """Persists the current session for this `cc_autotrageur` run."""
        session_row_object = InsertRowObject(
            CC_SESSION_TABLE,
            self._session._asdict(),
            (CC_SESSION_PRIM_KEY_ID,))

        db_handler.insert_row(session_row_object)
        db_handler.commit_all()

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
            buy_response['session_id'] = self._session.id
            buy_trade_row_obj = InsertRowObject(
                TRADES_TABLE,
                buy_response,
                (TRADES_PRIM_KEY_TRADE_OPP_ID, TRADES_PRIM_KEY_SIDE))
            db_handler.insert_row(buy_trade_row_obj)

        # Persist the executed sell order, if available.
        if sell_response is not None:
            sell_response['trade_opportunity_id'] = trade_opportunity_id
            sell_response['session_id'] = self._session.id
            sell_trade_row_obj = InsertRowObject(
                TRADES_TABLE,
                sell_response,
                (TRADES_PRIM_KEY_TRADE_OPP_ID, TRADES_PRIM_KEY_SIDE))
            db_handler.insert_row(sell_trade_row_obj)

        db_handler.commit_all()

    def __setup_dry_run_exchanges(self, resume_id):
        """Sets up DryRunExchanges which emulate Exchanges.  Trades, wallet
        balances, other exchange-related state is then recorded.

        Args:
            resume_id (str): The unique ID used to resume the bot from a
                previous run.

        Returns:
            (tuple(DryRunExchange, DryRunExchange)): The DryRunExchanges for
                E1 and E2 respectively.
        """
        if resume_id:
            dry_e1 = self._stat_tracker.dry_run_e1
            dry_e2 = self._stat_tracker.dry_run_e2
        else:
            e1_base, e1_quote = split_symbol(self._config.exchange1_pair)
            e2_base, e2_quote = split_symbol(self._config.exchange2_pair)
            exchange1 = self._config.exchange1
            exchange2 = self._config.exchange2
            e1_base_balance = self._config.dryrun_e1_base
            e1_quote_balance = self._config.dryrun_e1_quote
            e2_base_balance = self._config.dryrun_e2_base
            e2_quote_balance = self._config.dryrun_e2_quote
            dry_e1 = DryRunExchange(exchange1, e1_base, e1_quote,
                                    e1_base_balance, e1_quote_balance)
            dry_e2 = DryRunExchange(exchange2, e2_base, e2_quote,
                                    e2_base_balance, e2_quote_balance)
        return dry_e1, dry_e2

    def __setup_stat_tracker(self, resume_id=None):
        """Sets up the bot's StatTracker.

        Used for internal tracking and also for persisting simple statistics
        into the database for reporting and analysis.

        Args:
            resume_id (str, optional): The resume id used when resuming a run.
                Defaults to None.
        """
        new_stat_tracker_id = str(uuid.uuid4())
        if resume_id:
            if self._config.use_test_api:
                fancy_log("Resumed bot running against TEST Exchange APIs.")
            else:
                fancy_log("Resumed bot running against LIVE Exchange APIs.")

            if self._config.dryrun:
                fancy_log(
                    "Resumed - DRY RUN mode. Trades will NOT execute on actual "
                    "exchanges.")
        else:
            if self._config.dryrun:
                fancy_log(
                    "DRY RUN mode initiated. Trades will NOT execute on actual"
                    " exchanges.")

            self._stat_tracker = CCStatTracker(
                new_id=new_stat_tracker_id,
                e1_trader=self.trader1,
                e2_trader=self.trader2)

        row_data = {
            'id': new_stat_tracker_id,
            'session_id': self._session.id,
            'e1_start_bal_base': self.trader1.base_bal,
            'e1_close_bal_base': self.trader1.base_bal,
            'e2_start_bal_base': self.trader2.base_bal,
            'e2_close_bal_base': self.trader2.base_bal,
            'e1_start_bal_quote': self.trader1.quote_bal,
            'e1_close_bal_quote': self.trader1.quote_bal,
            'e2_start_bal_quote': self.trader2.quote_bal,
            'e2_close_bal_quote': self.trader2.quote_bal,
            'num_fatal_errors': 0,
            'trade_count': 0
        }
        stat_tracker_row_obj = InsertRowObject(
            CC_MEASURES_TABLE,
            row_data,
            (CC_MEASURES_PRIM_KEY_ID,))
        db_handler.insert_row(stat_tracker_row_obj)
        db_handler.commit_all()

    def __setup_traders(self, exchange_key_map, resume_id):
        """Sets up the Traders to interface with exchanges.

        Args:
            exchange_key_map (dict): A map containing authentication
                information necessary to connect with the exchange APIs.
            resume_id (str): The unique ID used to resume the bot from a
                previous run.

        Raises:
            AutotrageurAuthenticationError: Raised when given incorrect
                credentials or exchange unavailable when attempting to
                communicate through an exchange's API.
        """
        # TODO: Looks suitable for a design pattern here to create the Traders
        # as their creation is complex enough.

        # Extract the pairs.
        e1_base, e1_quote = split_symbol(self._config.exchange1_pair)
        e2_base, e2_quote = split_symbol(self._config.exchange2_pair)

        exchange1 = self._config.exchange1
        exchange2 = self._config.exchange2

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

        # Set up DryRunExchanges.
        if self._config.dryrun:
            dry_e1, dry_e2 = self.__setup_dry_run_exchanges(resume_id)
        else:
            dry_e1 = None
            dry_e2 = None

        self.trader1 = CCXTTrader(
            e1_base,
            e1_quote,
            exchange1,
            'e1',
            num_to_decimal(self._config.slippage),
            exchange1_configs,
            dry_e1)
        self.trader2 = CCXTTrader(
            e2_base,
            e2_quote,
            exchange2,
            'e2',
            num_to_decimal(self._config.slippage),
            exchange2_configs,
            dry_e2)

        # Set to run against test API, if applicable.
        if not self._config.use_test_api:
            fancy_log("Starting bot against LIVE exchange APIs.")
            self.is_test_run = False
        else:
            fancy_log("Starting bot against TEST exchange APIs.")
            self.trader1.connect_test_api()
            self.trader2.connect_test_api()
            self.is_test_run = True

        # Load the available markets for the exchange.
        self.trader1.load_markets()
        self.trader2.load_markets()

        try:
            # Dry run uses balances set in the configuration files.
            self.trader1.update_wallet_balances()
            self.trader2.update_wallet_balances()
        except (ccxt.AuthenticationError, ccxt.ExchangeNotAvailable) as auth_error:
            logging.error(auth_error)
            raise AutotrageurAuthenticationError(auth_error)

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
                    [subject, DEFAULT_PHONE_MESSAGE],
                    self.twilio_config[TWILIO_RECIPIENT_NUMBERS],
                    self.twilio_config[TWILIO_SENDER_NUMBER],
                    is_mock_call=self._config.dryrun or self.is_test_run)
            except Exception as exc:
                alert_error = True
                logging.debug("An error occurred trying to phone with twilio.")
                logging.error(exc, exc_info=True)

        if alert_error:
            raise AlertError("One or more methods of communication have"
                                " failed.  Check the logs for more detail.")

    # @Override
    def _clean_up(self):
        """Cleans up the state of the autotrageur."""
        self._strategy.clean_up()

    # @Override
    def _execute_trade(self):
        """Execute the trade, providing necessary failsafes."""
        buy_response = None
        sell_response = None
        trade_metadata = self._strategy.get_trade_data()

        if self._config.dryrun:
            logging.debug("**Dry run - begin fake execution")
            buy_response = arbseeker.execute_buy(
                trade_metadata.buy_trader,
                trade_metadata.buy_price)
            self._stat_tracker.trade_count += 1

            executed_amount = buy_response['post_fee_base']
            sell_response = arbseeker.execute_sell(
                trade_metadata.sell_trader,
                trade_metadata.sell_price,
                executed_amount)
            self._stat_tracker.trade_count += 1

            self._strategy.finalize_trade(buy_response, sell_response)
            self._stat_tracker.log_balances()
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
                self._stat_tracker.trade_count += 1

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
                    self._stat_tracker.trade_count += 1
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
        """Exports the state of the autotrageur to a database.

        NOTE: This method is only called when the cc bot is stops due to a
        fatal error or if it is killed manually."""
        logging.debug("#### Exporting bot's current state")

        # Update cc_sessions entry.
        session_update_result = db_handler.execute_parametrized_query(
            "UPDATE cc_session SET stop_timestamp = %s WHERE id = %s;",
            (int(time.time()), self._session.id))

        # UPDATE the cc_measures table with updated stats.
        measures_update_result = db_handler.execute_parametrized_query(
            "UPDATE cc_measures SET "
            "e1_close_bal_base = %s, "
            "e2_close_bal_base = %s, "
            "e1_close_bal_quote = %s, "
            "e2_close_bal_quote = %s, "
            "num_fatal_errors = num_fatal_errors + 1, "
            "trade_count = %s "
            "WHERE id = %s;", (
                self._stat_tracker.e1.base_bal,
                self._stat_tracker.e2.base_bal,
                self._stat_tracker.e1.quote_bal,
                self._stat_tracker.e2.quote_bal,
                self._stat_tracker.trade_count,
                self._stat_tracker.id))

        logging.debug("UPDATE cc_session affected rows: {}".format(
            session_update_result))
        logging.debug("UPDATE cc_measures affected rows: {}".format(
            measures_update_result))

        # Register copyreg.pickle with Checkpoint object and helper function
        # for better backwards-compatibility in pickling.
        # (See 'cc_checkpoint_utils' module for more details)
        copyreg.pickle(CCCheckpoint, pickle_cc_checkpoint)

        # Detach the Traders from StatTracker and attach it to the Checkpoint.
        self._stat_tracker.detach_traders()
        self.checkpoint.stat_tracker = self._stat_tracker

        # The generated ID can be used as the `resume_id` to resume the bot
        # from the saved state.
        cc_state_map = {
            'id': str(uuid.uuid4()),
            'session_id': self._session.id,
            'state': pickle.dumps(self.checkpoint)
        }
        logging.debug(
            "#### The exported checkpoint object is: {0!r}".format(
                self.checkpoint))
        logging.info("Exported with resume id: {}".format(
            cc_state_map[CC_STATE_PRIM_KEY_ID]))
        cc_state_row_obj = InsertRowObject(
            CC_STATE_TABLE,
            cc_state_map,
            (CC_STATE_PRIM_KEY_ID,))
        db_handler.insert_row(cc_state_row_obj)
        db_handler.commit_all()

        # Reattach the Traders for further use in current bot run.
        self._stat_tracker.attach_traders(self.trader1, self.trader2)

    # @Override
    def _final_log(self):
        """Outputs a final log and/or console output during teardown of the
        bot."""
        self._stat_tracker.log_all()

    # @Override
    def _import_state(self, resume_id):
        """Imports the state of a previous autotrageur run.

        Sets the CCCheckpoint to be a snapshot of the previous autotrageur's
        state.

        Args:
            resume_id (str): The unique ID used to resume the bot from a
                previous run.
        """
        logging.debug("#### Importing bot's previous state")
        raw_result = db_handler.execute_parametrized_query(
            "SELECT state FROM cc_state where id = %s;",
            (resume_id,))

        # The raw result comes back as a list of tuples.  We expect only
        # one result as the `autotrageur_resume_id` is unique per
        # export.
        previous_checkpoint = pickle.loads(raw_result[0][0])

        if not isinstance(previous_checkpoint, CCCheckpoint):
            raise IncorrectStateObjectTypeError(
                "CCCheckpoint is the required type.  {} type was given."
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
        - Traders to interface with exchange APIs (parses the keyfile for
            relevant authentication first)
        - Twilio Client

        Other responsibilities:
        - Persists Configuration and Session in the database.

        Args:
            arguments (dict): Map of the arguments passed to the program.
        """
        super()._post_setup(arguments)

        # Persist the configuration if required.
        if not arguments['--resume_id']:
            self.__persist_config()

        # Persist session.
        self.__persist_session()

        # Parse keyfile into a dict.
        exchange_key_map = self._parse_keyfile(
            arguments['KEYFILE'], arguments['--pi_mode'])

        # Set up the Traders for interfacing with exchange APIs.
        self.__setup_traders(exchange_key_map, arguments['--resume_id'])

        # Initialize StatTracker component and attach it to the Checkpoint.
        self.__setup_stat_tracker(arguments['--resume_id'])
        if arguments['--resume_id']:
            self._stat_tracker.attach_traders(self.trader1, self.trader2)

        # Set up Twilio Client.
        self._load_twilio(self._config.twilio_cfg_path)

    # @Override
    def _setup(self, arguments):
        """Initializes the autotrageur bot for use by setting up core
        components which must be set up before any additional components.

        In addition to superclass setup, the following core components are
        initialized:
        - Checkpoint (for state-related variables)
        - Algorithm
        - Dry Run (on resume)
        - Session

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
            self._stat_tracker = self.checkpoint.stat_tracker
            logging.debug(
                '#### Restored State objects: {0!r}\n{1!r}\n{2!r}'.format(
                    self._config,
                    self._strategy.state,
                    self._stat_tracker))
        else:
            # Initialize a Checkpoint object to hold state.
            self.checkpoint = CCCheckpoint(self._config)

            # Set up the Algorithm.
            self._strategy = self.__construct_strategy()

        self._session = CCSession(
            str(uuid.uuid4()), self._config.id, int(time.time()), None)

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
