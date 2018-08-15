import logging
import os
import pprint
import time
import traceback
import uuid
from decimal import Decimal

import ccxt
import schedule
import yaml

import bot.arbitrage.arbseeker as arbseeker
import libs.db.maria_db_handler as db_handler
import libs.twilio.twilio_client as twilio_client
from bot.common.config_constants import (DRYRUN, EMAIL_CFG_PATH, H_TO_E1_MAX,
                                         H_TO_E2_MAX, ID, SPREAD_MIN,
                                         START_TIMESTAMP, TWILIO_CFG_PATH,
                                         TWILIO_RECIPIENT_NUMBERS,
                                         TWILIO_SENDER_NUMBER, VOL_MIN)
from bot.common.db_constants import (FCF_AUTOTRAGEUR_CONFIG_COLUMNS,
                                     FCF_AUTOTRAGEUR_CONFIG_PRIM_KEY_ID,
                                     FCF_AUTOTRAGEUR_CONFIG_TABLE,
                                     FOREX_RATE_PRIM_KEY_ID, FOREX_RATE_TABLE,
                                     TRADE_OPPORTUNITY_PRIM_KEY_ID,
                                     TRADE_OPPORTUNITY_TABLE,
                                     TRADES_PRIM_KEY_SIDE,
                                     TRADES_PRIM_KEY_TRADE_OPP_ID,
                                     TRADES_TABLE)
from bot.common.decimal_constants import ONE
from bot.common.enums import Momentum
from libs.twilio.twilio_client import TwilioClient
from bot.trader.ccxt_trader import OrderbookException
from libs.db.maria_db_handler import InsertRowObject
from libs.email_client.simple_email_client import send_all_emails
from libs.fiat_symbols import FIAT_SYMBOLS
from libs.utilities import num_to_decimal

from .autotrageur import Autotrageur


class AuthenticationError(Exception):
    """Incorrect credentials or exchange unavailable."""
    pass


class IncompleteArbitrageError(Exception):
    """Error indicating an uneven buy/sell base amount."""
    pass


class FCFCheckpoint():
    """Contains the current algorithm state.

    Encapsulates values pertaining to the algorithm.  Useful for rollback
    situations.
    """
    def __init__(self):
        """Constructor."""
        self.has_started = False
        self.momentum = None
        self.e1_targets = None
        self.e2_targets = None
        self.target_index = None
        self.last_target_index = None
        self.h_to_e1_max = None
        self.h_to_e2_max = None

    def save(self, autotrageur):
        """Saves the current autotrageur state before another algorithm
        iteration.

        Args:
            autotrageur (FCFAutotrageur): The current FCFAutotrageur.
        """
        self.has_started = autotrageur.has_started
        self.momentum = autotrageur.momentum
        self.e1_targets = autotrageur.e1_targets
        self.e2_targets = autotrageur.e2_targets
        self.target_index = autotrageur.target_index
        self.last_target_index = autotrageur.last_target_index
        self.h_to_e1_max = autotrageur.h_to_e1_max
        self.h_to_e2_max = autotrageur.h_to_e2_max

    def restore(self, autotrageur):
        """Restores the saved autotrageur state.

        Args:
            autotrageur (FCFAutotrageur): The current FCFAutotrageur.
        """
        autotrageur.has_started = self.has_started
        autotrageur.momentum = self.momentum
        autotrageur.e1_targets = self.e1_targets
        autotrageur.e2_targets = self.e2_targets
        autotrageur.target_index = self.target_index
        autotrageur.last_target_index = self.last_target_index
        autotrageur.h_to_e1_max = self.h_to_e1_max
        autotrageur.h_to_e2_max = self.h_to_e2_max


class InsufficientCryptoBalance(Exception):
    """Thrown when there is not enough crypto balance to fulfill the matching
    sell order."""
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

    def __advance_target_index(self, spread, targets):
        """Increment the target index to minimum target greater than
        spread.

        Args:
            spread (Decimal): The calculated spread.
            targets (list): The list of targets.
        """
        while (self.target_index + 1 < len(targets) and
                spread >= targets[self.target_index + 1][0]):
            logging.debug('#### target_index before: {}'.format(self.target_index))
            self.target_index += 1
            logging.debug('#### target_index after: {}'.format(self.target_index))

    def __calc_targets(self, spread, h_max, from_balance):
        """Calculate the target spreads and cash positions.

        Args:
            spread (Decimal): The calculated spread.
            h_max (Decimal): The historical maximum spread.
            from_balance (Decimal): The balance on the buy exchange.

        Returns:
            list: The list of (spread, cash position) tuple targets.
        """
        t_num = int((h_max - spread) / self.spread_min)

        if t_num <= 1:
            # Volume should be calculated with leftover wallet balance at this
            # point as we've reached the h_to_e1_max.
            targets = [(
                max(h_max, spread + self.spread_min),
                from_balance
            )]
            return targets

        inc = (h_max - spread) / num_to_decimal(t_num)
        x = (from_balance / self.vol_min) ** (ONE / (t_num - ONE))
        targets = []
        for i in range(1, t_num + 1):
            if self.vol_min >= from_balance:
                # Min vol will empty from_balance on buying exchange.
                position = from_balance
            else:
                position = self.vol_min * (x ** (num_to_decimal(i) - ONE))
            targets.append((spread + num_to_decimal(i) * inc, position))

        return targets

    def __evaluate_to_e1_trade(self, momentum_change, spread_opp):
        """Changes state information to prepare for the trades from e2
        to e1.

        Args:
            momentum_change (bool): Whether there was a momentum change.
            spread_opp (SpreadOpportunity): The spread and price info.
        """
        self.__advance_target_index(spread_opp.e1_spread, self.e1_targets)
        self.__prepare_trade(
            momentum_change,
            self.trader2,
            self.trader1,
            self.e1_targets,
            spread_opp)

    def __evaluate_to_e2_trade(self, momentum_change, spread_opp):
        """Changes state information to prepare for the trades from e1
        to e2.

        Args:
            momentum_change (bool): Whether there was a momentum change.
            spread_opp (SpreadOpportunity): The spread and price info.
        """
        self.__advance_target_index(spread_opp.e2_spread, self.e2_targets)
        self.__prepare_trade(
            momentum_change,
            self.trader1,
            self.trader2,
            self.e2_targets,
            spread_opp)

    def __is_trade_opportunity(self, spread_opp):
        """Evaluate spread numbers against targets and set up state for
        trade execution.

        Args:
            spread_opp (SpreadOpportunity): The spread and price info.

        Returns:
            bool: Whether there is a trade opportunity.
        """
        if self.momentum is Momentum.NEUTRAL:
            if (self.target_index < len(self.e2_targets) and
                    spread_opp.e2_spread >= self.e2_targets[self.target_index][0]):
                self.__evaluate_to_e2_trade(True, spread_opp)
                self.momentum = Momentum.TO_E2
                return True
            elif (self.target_index < len(self.e1_targets) and
                    spread_opp.e1_spread >= self.e1_targets[self.target_index][0]):
                self.__evaluate_to_e1_trade(True, spread_opp)
                self.momentum = Momentum.TO_E1
                return True
        elif self.momentum is Momentum.TO_E2:
            if (self.target_index < len(self.e2_targets) and
                    spread_opp.e2_spread >= self.e2_targets[self.target_index][0]):
                self.__evaluate_to_e2_trade(False, spread_opp)
                return True
            # Momentum change from TO_E2 to TO_E1.
            elif spread_opp.e1_spread >= self.e1_targets[0][0]:
                self.target_index = 0
                logging.debug('#### Momentum changed from TO_E2 to TO_E1')
                logging.debug('#### TO_E1 spread: {} > First TO_E1 target {}'.\
                    format(spread_opp.e1_spread, self.e1_targets[0][0]))
                self.__evaluate_to_e1_trade(True, spread_opp)
                self.momentum = Momentum.TO_E1
                return True
        elif self.momentum is Momentum.TO_E1:
            # Momentum change from TO_E1 to TO_E2.
            if spread_opp.e2_spread >= self.e2_targets[0][0]:
                self.target_index = 0
                logging.debug('#### Momentum changed from TO_E1 to TO_E2')
                logging.debug('#### TO_E2 spread: {} > First TO_E2 target {}'.\
                    format(spread_opp.e2_spread, self.e2_targets[0][0]))
                self.__evaluate_to_e2_trade(True, spread_opp)
                self.momentum = Momentum.TO_E2
                return True
            elif (self.target_index < len(self.e1_targets) and
                    spread_opp.e1_spread >= self.e1_targets[self.target_index][0]):
                self.__evaluate_to_e1_trade(False, spread_opp)
                return True

        return False

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

    def __persist_configs(self):
        """Persists the configuration for this `fcf_autotrageur` run."""
        # Add extra config entries for database persistence.
        self.config[START_TIMESTAMP] = int(time.time())
        self.config[ID] = str(uuid.uuid4())

        fcf_autotrageur_config_row = db_handler.build_row(
            FCF_AUTOTRAGEUR_CONFIG_COLUMNS, self.config)
        config_row_obj = InsertRowObject(
            FCF_AUTOTRAGEUR_CONFIG_TABLE,
            fcf_autotrageur_config_row,
            (FCF_AUTOTRAGEUR_CONFIG_PRIM_KEY_ID, ))

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

    def __persist_trade_data(self, buy_response, sell_response):
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
        """
        # Persist the spread_opp.
        trade_opportunity_id = self.trade_metadata['spread_opp'].id
        spread_opp = self.trade_metadata['spread_opp']._asdict()
        trade_opp_row_obj = InsertRowObject(
            TRADE_OPPORTUNITY_TABLE,
            spread_opp,
            (TRADE_OPPORTUNITY_PRIM_KEY_ID, ))
        db_handler.insert_row(trade_opp_row_obj)

        # Persist the executed buy order, if available.
        if buy_response is not None:
            buy_response['trade_opportunity_id'] = trade_opportunity_id
            buy_response['autotrageur_config_id'] = self.config[ID]
            buy_trade_row_obj = InsertRowObject(
                TRADES_TABLE,
                buy_response,
                (TRADES_PRIM_KEY_TRADE_OPP_ID, TRADES_PRIM_KEY_SIDE))
            db_handler.insert_row(buy_trade_row_obj)

        # Persist the executed sell order, if available.
        if sell_response is not None:
            sell_response['trade_opportunity_id'] = trade_opportunity_id
            sell_response['autotrageur_config_id'] = self.config[ID]
            sell_trade_row_obj = InsertRowObject(
                TRADES_TABLE,
                sell_response,
                (TRADES_PRIM_KEY_TRADE_OPP_ID, TRADES_PRIM_KEY_SIDE))
            db_handler.insert_row(sell_trade_row_obj)

        db_handler.commit_all()

    def __prepare_trade(self, is_momentum_change, buy_trader, sell_trader,
                        targets, spread_opp):
        """Set up trade metadata and update target indices.

        Args:
            is_momentum_change (bool): Whether this is the first trade
                after a momentum change.
            buy_trader (CCXTTrader): The trader to buy with.
            sell_trader (CCXTTrader): The trader to sell with.
            targets (list): The 'to_sell_exchange' targets.
            spread_opp (SpreadOpportunity): The spread and price info.

        Raises:
            InsufficientCryptoBalance: If crypto balance on the sell
                exchange is not enough to cover the buy target.
        """
        if self.target_index >= 1 and not is_momentum_change:
            trade_vol = targets[self.target_index][1] - \
                targets[self.last_target_index][1]
        else:
            trade_vol = targets[self.target_index][1]

        # NOTE: Trader's `quote_target_amount` is updated here.  We need to use
        # the quote balance in case of intra-day forex fluctuations which
        # would result in an inaccurate USD balance.
        target_quote_amount = min(
            buy_trader.get_quote_from_usd(trade_vol),
            buy_trader.quote_bal)
        buy_trader.set_target_amounts(target_quote_amount, is_usd=False)

        if buy_trader is self.trader1:
            buy_price = spread_opp.e1_buy
            sell_price = spread_opp.e2_sell
        else:
            buy_price = spread_opp.e2_buy
            sell_price = spread_opp.e1_sell

        self.trade_metadata = {
            'spread_opp': spread_opp,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'buy_trader': buy_trader,
            'sell_trader': sell_trader
        }

        required_base = (
            buy_trader.quote_target_amount / self.trade_metadata['buy_price'])
        if (required_base > sell_trader.base_bal):
            exc_msg = ("Insufficient crypto balance on: {}.\n"
                       "Required base: {}\n"
                       "Actual base: {}")
            raise InsufficientCryptoBalance(
                exc_msg.format(
                    sell_trader.exchange_name, required_base,
                    sell_trader.base_bal))

        self.last_target_index = self.target_index
        self.target_index += 1
        logging.debug('#### target_index advanced by one, is now: {}'.format(
            self.target_index))

    def __update_trade_targets(self):
        """Updates the trade targets based on the direction of the completed
        trade.  E.g. If the trade was performed from e1 -> e2, then the
        `e1_targets` should be updated, vice versa.

        NOTE: Trade targets should only be updated if a trade was completely
        successful (buy and sell trades completed).
        """
        if self.trade_metadata['buy_trader'] is self.trader2:
            self.e2_targets = self.__calc_targets(
                self.trade_metadata['spread_opp'].e2_spread, self.h_to_e2_max,
                self.trader1.get_usd_balance())
            logging.debug("#### New calculated e2_targets: {}".format(
                list(enumerate(self.e2_targets))))
        else:
            self.e1_targets = self.__calc_targets(
                self.trade_metadata['spread_opp'].e1_spread, self.h_to_e1_max,
                self.trader2.get_usd_balance())
            logging.debug("#### New calculated e1_targets: {}".format(
                list(enumerate(self.e1_targets))))

    def __check_within_limits(self):
        """Check whether potential trade meets minimum volume limits.

        Should be used only when trade_metadata is set and there is a
        potential trade.

        Returns:
            bool: Whether the trade falls within the limits.
        """
        buy_trader = self.trade_metadata['buy_trader']
        sell_trader = self.trade_metadata['sell_trader']
        min_base_buy = buy_trader.get_min_base_limit()
        min_base_sell = sell_trader.get_min_base_limit()
        min_target_amount = (self.trade_metadata['buy_price']
                                * max(min_base_buy, min_base_sell))
        return buy_trader.quote_target_amount > min_target_amount

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
            dryrun=self.config[DRYRUN])

    def _clean_up(self):
        """Cleans up the state of the autotrageur before performing next
        actions which may be harmed by previous state."""
        self.trade_metadata = None

    def _execute_trade(self):
        """Execute the arbitrage."""
        buy_response = None
        sell_response = None

        if self.config[DRYRUN]:
            logging.debug("**Dry run - begin fake execution")
            buy_response = arbseeker.execute_buy(
                self.trade_metadata['buy_trader'],
                self.trade_metadata['buy_price'])

            executed_amount = buy_response['post_fee_base']
            sell_response = arbseeker.execute_sell(
                self.trade_metadata['sell_trader'],
                self.trade_metadata['sell_price'],
                executed_amount)
            self.trader1.update_wallet_balances(is_dry_run=True)
            self.trader2.update_wallet_balances(is_dry_run=True)
            self.__update_trade_targets()
            self.dry_run.log_balances()
            self.__persist_trade_data(buy_response, sell_response)
            logging.debug("**Dry run - end fake execution")
        else:
            try:
                buy_response = arbseeker.execute_buy(
                    self.trade_metadata['buy_trader'],
                    self.trade_metadata['buy_price'])
                bought_amount = buy_response['post_fee_base']
            except Exception as exc:
                self._send_email("BUY ERROR ALERT - CONTINUING", repr(exc))
                logging.error(exc, exc_info=True)
                self.checkpoint.restore(self)
            else:
                # If an exception is thrown, we want the program to stop on the
                # second trade.
                try:
                    sell_response = arbseeker.execute_sell(
                        self.trade_metadata['sell_trader'],
                        self.trade_metadata['sell_price'],
                        bought_amount)

                    sell_trader = self.trade_metadata['sell_trader']
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
                    # Retrieve updated wallet balances if everything worked
                    # as expected.
                    self.trader1.update_wallet_balances()
                    self.trader2.update_wallet_balances()

                    # Calculate the targets after the potential trade so that the wallet
                    # balances are the most up to date for the target amounts.
                    self.__update_trade_targets()
                    self._send_email(
                        "TRADE SUMMARY",
                        "Buy results:\n\n{}\n\nSell results:\n\n{}\n".format(
                            pprint.pformat(buy_response),
                            pprint.pformat(sell_response)))
            finally:
                self.__persist_trade_data(buy_response, sell_response)

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
        # Set trader target amounts based on strategy.
        self.trader1.set_target_amounts(
            max(self.vol_min, self.trader1.get_usd_balance()))
        self.trader2.set_target_amounts(
            max(self.vol_min, self.trader2.get_usd_balance()))

        try:
            spread_opp = arbseeker.get_spreads_by_ob(
                self.trader1, self.trader2)
        except (ccxt.NetworkError, OrderbookException) as exc:
            logging.error(exc, exc_info=True)
            return False

        is_opportunity = False

        if not self.has_started:
            self.momentum = Momentum.NEUTRAL

            self.e1_targets = self.__calc_targets(spread_opp.e1_spread,
                self.h_to_e1_max, self.trader2.get_usd_balance())
            logging.debug('#### Initial e1_targets: {}'.format(
                list(enumerate(self.e1_targets))))
            self.e2_targets = self.__calc_targets(spread_opp.e2_spread,
                self.h_to_e2_max, self.trader1.get_usd_balance())
            logging.debug('#### Initial e2_targets: {}'.format(
                list(enumerate(self.e2_targets))))

            self.target_index = 0
            self.last_target_index = 0
            self.has_started = True
        else:
            # Save the autotrageur state before proceeding with algorithm.
            self.checkpoint.save(self)
            if self.__is_trade_opportunity(spread_opp):
                logging.debug('#### Is a trade opportunity')
                is_opportunity = self.__check_within_limits()
                logging.debug('#### Is within exchange limits: {}'.format(is_opportunity))

        self.h_to_e1_max = max(self.h_to_e1_max, spread_opp.e1_spread)
        self.h_to_e2_max = max(self.h_to_e2_max, spread_opp.e2_spread)

        return is_opportunity

    def _send_email(self, subject, msg):
        """Send email alert to preconfigured emails.

        Args:
            subject (str): The subject of the message.
            msg (str): The contents of the email to send out.
        """
        send_all_emails(self.config[EMAIL_CFG_PATH], subject, msg)

    # @Override
    def _setup(self):
        """Sets up the algorithm to use.

        Raises:
            AuthenticationError: If not dryrun and authentication fails.
        """
        super()._setup()

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
        try:
            # Dry run uses balances set in the configuration files.
            self.trader1.update_wallet_balances(is_dry_run=self.config[DRYRUN])
            self.trader2.update_wallet_balances(is_dry_run=self.config[DRYRUN])
        except (ccxt.AuthenticationError, ccxt.ExchangeNotAvailable) as auth_error:
            logging.error(auth_error)
            raise AuthenticationError(auth_error)

        self.__persist_configs()
        self.has_started = False
        self.spread_min = num_to_decimal(self.config[SPREAD_MIN])
        self.vol_min = num_to_decimal(self.config[VOL_MIN])
        self.h_to_e1_max = num_to_decimal(self.config[H_TO_E1_MAX])
        self.h_to_e2_max = num_to_decimal(self.config[H_TO_E2_MAX])
        self.checkpoint = FCFCheckpoint()
