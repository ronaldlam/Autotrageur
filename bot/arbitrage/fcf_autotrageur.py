import logging
from decimal import Decimal

import ccxt

import bot.arbitrage.arbseeker as arbseeker
from bot.common.config_constants import (DRYRUN, EMAIL_CFG_PATH, MAX_EMAILS,
    SPREAD_ROUNDING, SPREAD_TOLERANCE, SPREAD_MIN, VOL_MIN, H_TO_E1_MAX,
    H_TO_E2_MAX)
from bot.common.enums import Momentum
from libs.email_client.simple_email_client import send_all_emails
from libs.utilities import (num_to_decimal, set_autotrageur_decimal_context,
                            set_human_friendly_decimal_context)

from .autotrageur import Autotrageur


# Global module variables.
prev_spread = Decimal('0')
email_count = 0
DECIMAL_ONE = num_to_decimal('1')


# Email message constants.
EMAIL_HIGH_SPREAD_HEADER = "Subject: Arb Forward-Spread Alert!\nThe spread of "
EMAIL_LOW_SPREAD_HEADER = "Subject: Arb Backward-Spread Alert!\nThe spread of "
EMAIL_NONE_SPREAD = "No arb opportunity found."


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
    @staticmethod
    def _is_within_tolerance(curr_spread, prev_spread, spread_rnd,
                              spread_tol):
        """Compares the current spread with the previous spread to see if
        within user-specified spread tolerance.

        If rounding specified (spread_rnd), the current and previous spreads
        will be rounded before check against tolerance.

        Args:
            curr_spread (Decimal): The current spread of the arb opportunity.
            prev_spread (Decimal): The previous spread to compare to.
            spread_rnd (int): Number of decimals to round the spreads to.
            spread_tol (Decimal): The spread tolerance to check if curr_spread
                minus prev_spread is within.

        Returns:
            bool: True if the (current spread - previous spread) is still
                within the tolerance.  Else, False.
        """
        set_human_friendly_decimal_context()

        if spread_rnd is not None:
            logging.info("Rounding spreads to %d decimal place", spread_rnd)
            curr_spread = round(curr_spread, spread_rnd)
            prev_spread = round(prev_spread, spread_rnd)

        logging.info("\nPrevious spread of: %f Current spread of: %f\n"
                     "spread tolerance of: %f", prev_spread, curr_spread,
                     spread_tol)

        within_tolerance = (abs(curr_spread - prev_spread) <= spread_tol)

        set_autotrageur_decimal_context()

        return within_tolerance

    def __advance_target_index(self, spread, targets):
        """Increment the target index to minimum target greater than
        spread.

        Args:
            spread (Decimal): The calculated spread.
            targets (list): The list of targets.
        """
        while (self.target_index + 1 < len(targets) and
                spread >= targets[self.target_index + 1][0]):
            self.target_index += 1

    # def __set_message(self, opp_type):
    #     """Sets the message used for emails and logging based on the type of
    #     spread opportunity.

    #     Args:
    #         opp_type (SpreadOpportunity): A classification of the spread
    #             opportunity present.
    #     """
    #     if opp_type is SpreadOpportunity.LOW:
    #         self.message = (
    #             EMAIL_LOW_SPREAD_HEADER
    #             + self.exchange1_basequote[0]
    #             + " is "
    #             + str(self.spread_opp[arbseeker.SPREAD]))
    #     elif opp_type is SpreadOpportunity.HIGH:
    #         self.message = (
    #             EMAIL_HIGH_SPREAD_HEADER
    #             + self.exchange1_basequote[0]
    #             + " is "
    #             + str(self.spread_opp[arbseeker.SPREAD]))
    #     else:
    #         self.message = EMAIL_NONE_SPREAD

    def __email_or_throttle(self, curr_spread):
        """Sends emails for a new arbitrage opportunity.  Throttles if too
        frequent.

        Based on preference of SPREAD_ROUNDING, SPREAD_TOLERANCE and MAX_EMAILS,
        an e-mail will be sent if the current spread is not similar to previous
        spread AND if a max email threshold has not been hit with similar
        spreads.

        Args:
            curr_spread (Decimal): The current arbitrage spread for the arbitrage
                opportunity.
        """
        global prev_spread
        global email_count

        max_num_emails = self.config[MAX_EMAILS]
        spread_tol = num_to_decimal(self.config[SPREAD_TOLERANCE])
        spread_rnd = self.config[SPREAD_ROUNDING]

        within_tolerance = FCFAutotrageur._is_within_tolerance(
            curr_spread, prev_spread, spread_rnd, spread_tol)

        if not within_tolerance or email_count < max_num_emails:
            if email_count == max_num_emails:
                email_count = 0
            prev_spread = curr_spread

            # Continue running bot even if unable to send e-mail.
            try:
                send_all_emails(self.config[EMAIL_CFG_PATH], self.message)
            except Exception:
                logging.error(
                    "Unable to send e-mail due to: \n", exc_info=True)
            email_count += 1

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
        x = (from_balance / self.vol_min) ** (DECIMAL_ONE / (t_num - DECIMAL_ONE))
        targets = []
        for i in range(1, t_num + 1):
            if self.vol_min >= from_balance:
                # Min vol will empty from_balance on buying exchange.
                position = from_balance
            else:
                position = self.vol_min * (x ** (num_to_decimal(i) - DECIMAL_ONE))
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
            self.tclient2,
            self.tclient1,
            self.e1_targets,
            spread_opp)
        self.e2_targets = self.__calc_targets(
            spread_opp.e2_spread, self.h_to_e2_max, self.tclient1.quote_bal)

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
            self.tclient1,
            self.tclient2,
            self.e2_targets,
            spread_opp)
        self.e1_targets = self.__calc_targets(
            spread_opp.e1_spread, self.h_to_e1_max, self.tclient2.quote_bal)

    def __evaluate_spread(self, spread_opp):
        """Evaluate spread numbers for

        Args:
            spread_opp (SpreadOpportunity): The spread and price info.

        Returns:
            bool: Whether there is a trade opportunity
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
            # momentum change
            elif spread_opp.e1_spread >= self.e1_targets[0][0]:
                self.target_index = 0
                self.__evaluate_to_e1_trade(True, spread_opp)
                self.momentum = Momentum.TO_E1
                return True
        elif self.momentum is Momentum.TO_E1:
            # momentum change
            if spread_opp.e2_spread >= self.e2_targets[0][0]:
                self.target_index = 0
                self.__evaluate_to_e2_trade(True, spread_opp)
                self.momentum = Momentum.TO_E2
                return True
            elif (self.target_index < len(self.e1_targets) and
                    spread_opp.e1_spread >= self.e1_targets[self.target_index][0]):
                self.__evaluate_to_e1_trade(False, spread_opp)
                return True

        return False

    def __prepare_trade(self, is_momentum_change, buy_trader, sell_trader,
                        targets, spread_opp):
        if self.target_index >= 1 and not is_momentum_change:
            trade_vol = targets[self.target_index][1] - \
                targets[self.last_target_index][1]
        else:
            trade_vol = targets[self.target_index][1]

        # NOTE: Trader's `quote_target_amount` is updated here.
        buy_trader.quote_target_amount = min(trade_vol, buy_trader.quote_bal)
        if buy_trader is self.tclient1:
            self.trade_metadata = {
                'buy_price': spread_opp.e1_buy,
                'sell_price': spread_opp.e2_sell,
                'buy_trader': buy_trader,
                'sell_trader': sell_trader
            }
        else:
            self.trade_metadata = {
                'buy_price': spread_opp.e2_buy,
                'sell_price': spread_opp.e1_sell,
                'buy_trader': sell_trader,
                'sell_trader': buy_trader
            }

        if (buy_trader.quote_target_amount / self.trade_metadata['buy_price']
                > sell_trader.base_bal):
            raise InsufficientCryptoBalance(
                "Insufficient crypto balance on: {}".format(
                    sell_trader.exchange_name))

        self.last_target_index = self.target_index
        self.target_index += 1

    def _clean_up(self):
        """Cleans up the state of the autotrageur before performing next
        actions which may be harmed by previous state."""
        self.message = None

    def _execute_trade(self):
        """Execute the arbitrage."""
        # TODO: Evaluate options and implement retry logic.
        if self.config[DRYRUN]:
            logging.info("**Dry run - begin fake execution")
            arbseeker.execute_arbitrage(self.trade_metadata)
            logging.info("**Dry run - end fake execution")
        else:
            logging.info("Attempting to execute trades")
            if arbseeker.execute_arbitrage(self.trade_metadata):
                self.tclient1.fetch_wallet_balances()
                self.tclient2.fetch_wallet_balances()
            else:
                logging.info("Trade was not executed.")

    def _poll_opportunity(self):
        """Poll exchanges for arbitrage opportunity.

        Returns:
            bool: Whether there is an opportunity.
        """
        # Set quote target amount based on strategy.
        self.tclient1.quote_target_amount = max(self.vol_min, self.tclient1.quote_bal)
        self.tclient2.quote_target_amount = max(self.vol_min, self.tclient2.quote_bal)

        try:
            spread_opp = arbseeker.get_spreads_by_ob(
                self.tclient1, self.tclient2)
        except ccxt.NetworkError as network_error:
            logging.error(network_error, exc_info=True)
            return False

        is_opportunity = False

        if not self.has_started:
            self.momentum = Momentum.NEUTRAL

            self.e1_targets = self.__calc_targets(spread_opp.e1_spread,
                self.h_to_e1_max, self.tclient2.quote_bal)
            self.e2_targets = self.__calc_targets(spread_opp.e2_spread,
                self.h_to_e2_max, self.tclient1.quote_bal)
            logging.info('-----To %s targets: %s' %
                (self.tclient1.exchange_name, self.e1_targets))
            logging.info('-----To %s targets: %s' %
                (self.tclient2.exchange_name, self.e2_targets))

            self.target_index = 0
            self.last_target_index = 0
            self.has_started = True
        else:
            is_opportunity = self.__evaluate_spread(spread_opp)

        self.h_to_e1_max = max(self.h_to_e1_max, spread_opp.e1_spread)
        self.h_to_e2_max = max(self.h_to_e2_max, spread_opp.e2_spread)

        return is_opportunity

    # @Override
    def _setup_markets(self):
        """Set up the market objects for the algorithm to use.

        Raises:
            AuthenticationError: If not dryrun and authentication fails.
        """
        super()._setup_markets()
        self.spread_min = num_to_decimal(self.config[SPREAD_MIN])
        self.vol_min = num_to_decimal(self.config[VOL_MIN])
        self.h_to_e1_max = num_to_decimal(self.config[H_TO_E1_MAX])
        self.h_to_e2_max = num_to_decimal(self.config[H_TO_E2_MAX])
