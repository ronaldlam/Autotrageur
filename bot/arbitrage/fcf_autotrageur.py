from decimal import Decimal
from enum import Enum
import logging

import ccxt

from .autotrageur import Autotrageur
import bot.arbitrage.arbseeker as arbseeker
from bot.common.config_constants import (SPREAD_TARGET_HIGH, SPREAD_TARGET_LOW,
    DRYRUN, EMAIL_CFG_PATH, MAX_EMAILS, SPREAD_ROUNDING, SPREAD_TOLERANCE)
from bot.common.enums import SpreadOpportunity
from libs.email_client.simple_email_client import send_all_emails


# Global module variables.
prev_spread = 0
email_count = 0


# Email message constants.
EMAIL_HIGH_SPREAD_HEADER = "Subject: Arb Forward-Spread Alert!\nThe spread of "
EMAIL_LOW_SPREAD_HEADER = "Subject: Arb Backward-Spread Alert!\nThe spread of "
EMAIL_NONE_SPREAD = "No arb opportunity found."


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
            curr_spread (float): The current spread of the arb opportunity.
            prev_spread (float): The previous spread to compare to.
            spread_rnd (int): Number of decimals to round the spreads to.
            spread_tol (float): The spread tolerance to check if curr_spread
                minus prev_spread is within.

        Returns:
            bool: True if the (current spread - previous spread) is still
                within the tolerance.  Else, False.
        """
        if spread_rnd is not None:
            logging.info("Rounding spreads to %d decimal place", spread_rnd)
            curr_spread = round(curr_spread, spread_rnd)
            prev_spread = round(prev_spread, spread_rnd)

        logging.info("\nPrevious spread of: %f Current spread of: %f\n"
                     "spread tolerance of: %f", prev_spread, curr_spread,
                     spread_tol)
        return (abs(Decimal(str(curr_spread)) - Decimal(str(prev_spread))) <=
                spread_tol)

    def _clean_up(self):
        """Cleans up the state of the autotrageur before performing next
        actions which may be harmed by previous state."""
        self.spread_opp = None
        self.message = None

    def __set_message(self, opp_type):
        """Sets the message used for emails and logging based on the type of
        spread opportunity.

        Args:
            opp_type (SpreadOpportunity): A classification of the spread
                opportunity present.
        """
        if opp_type is SpreadOpportunity.LOW:
            self.message = (
                EMAIL_LOW_SPREAD_HEADER
                + self.exchange1_basequote[0]
                + " is "
                + str(self.spread_opp[arbseeker.SPREAD]))
        elif opp_type is SpreadOpportunity.HIGH:
            self.message = (
                EMAIL_HIGH_SPREAD_HEADER
                + self.exchange1_basequote[0]
                + " is "
                + str(self.spread_opp[arbseeker.SPREAD]))
        else:
            self.message = EMAIL_NONE_SPREAD

    def __email_or_throttle(self, curr_spread):
        """Sends emails for a new arbitrage opportunity.  Throttles if too
        frequent.

        Based on preference of SPREAD_ROUNDING, SPREAD_TOLERANCE and MAX_EMAILS,
        an e-mail will be sent if the current spread is not similar to previous
        spread AND if a max email threshold has not been hit with similar
        spreads.

        Args:
            curr_spread (float): The current arbitrage spread for the arbitrage
                opportunity.
        """
        global prev_spread
        global email_count

        max_num_emails = self.config[MAX_EMAILS]
        spread_tol = self.config[SPREAD_TOLERANCE]
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

    def _poll_opportunity(self):
        """Poll exchanges for arbitrage opportunity.

        Note that self.message is set depending on the results of poll.
        This is specific for this implementation.

        Returns:
            bool: Whether there is an opportunity.
        """
        # TODO: Evaluate options and implement retry logic.
        try:
            # Get spread low and highs.
            spread_low = self.config[SPREAD_TARGET_LOW]
            spread_high = self.config[SPREAD_TARGET_HIGH]
            self.spread_opp = arbseeker.get_arb_opportunities_by_orderbook(
                self.tclient1, self.tclient2, spread_low,
                spread_high)
        except ccxt.NetworkError as network_error:
            logging.error(network_error, exc_info=True)
        finally:
            if self.spread_opp is None:
                self.__set_message(None)
                logging.log(logging.INFO, self.message)
                return False

            self.__set_message(self.spread_opp[arbseeker.SPREAD_OPP_TYPE])
            return True

    def _execute_trade(self):
        """Execute the trade, providing necessary failsafes."""
        # TODO: Evaluate options and implement retry logic.
        try:
            logging.info(self.message)
            self.__email_or_throttle(self.spread_opp[arbseeker.SPREAD])

            if self.config[DRYRUN]:
                logging.info("**Dry run - begin fake execution")
                arbseeker.execute_arbitrage(self.spread_opp)
                logging.info("**Dry run - end fake execution")
            else:
                verify = input("Type 'execute' to attempt trade execution\n")

                if verify == "execute":
                    logging.info("Attempting to execute trades")
                    arbseeker.execute_arbitrage(self.spread_opp)
                else:
                    logging.info("Trade was not executed.")
        except ccxt.NetworkError as network_err:
            logging.error(network_err, exc_info=True)
        except arbseeker.AbortTradeException as abort_trade:
            logging.error(abort_trade, exc_info=True)
