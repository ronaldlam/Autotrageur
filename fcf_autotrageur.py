import logging

import ccxt

from autotrageur import SPREAD_TARGET_HIGH, SPREAD_TARGET_LOW, AUTHENTICATE
from autotrageur import Autotrageur
import bot.arbitrage.arbseeker as arbseeker
from libs.email_client.simple_email_client import send_all_emails

class FCFAutotrageur(Autotrageur):
    """The fiat-crypto-fiat Autotrageur.

    This implementation of the Autotrageur polls two specified fiat to
    crypto markets. Given the target high and low spreads between the
    fiat currencies, this algorithm will execute a trade in the
    direction of exchange two (buy cypto on exchange one, sell crypto on
    exchange two) if the calculated spread is greater than the specified
    target high; vice versa if the calculated spread is less than the
    specified target low.
    """

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
        except ccxt.RequestTimeout as timeout:
            logging.error(timeout)
            return False
        finally:
            if self.spread_opp is None:
                self.message = "No arb opportunity found."
                logging.log(logging.INFO, self.message)
                return False
            elif self.spread_opp[arbseeker.SPREAD_HIGH]:
                self.message = (
                    "Subject: Arb Forward-Spread Alert!\nThe spread of "
                    + self.exchange1_basequote[0]
                    + " is "
                    + str(self.spread_opp[arbseeker.SPREAD]))
            else:
                self.message = (
                    "Subject: Arb Backward-Spread Alert!\nThe spread of "
                    + self.exchange1_basequote[0]
                    + " is "
                    + str(self.spread_opp[arbseeker.SPREAD]))
            return True

    def _execute_trade(self):
        """Execute the trade, providing necessary failsafes."""
        # TODO: Evaluate options and implement retry logic.
        try:
            if self.config[AUTHENTICATE]:
                logging.info(self.message)
                send_all_emails(self.message)
                verify = input("Type 'execute' to attempt trade execution\n")

                if verify == "execute":
                    logging.info("Attempting to execute trades")
                    arbseeker.execute_arbitrage(self.spread_opp)
                else:
                    logging.info("Trade was not executed.")
        except ccxt.RequestTimeout as timeout:
            logging.error(timeout)
        except arbseeker.AbortTradeException as abort_trade:
            logging.error(abort_trade)
