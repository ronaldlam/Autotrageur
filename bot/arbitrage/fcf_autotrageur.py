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
            self.trader2,
            self.trader1,
            self.e1_targets,
            spread_opp)
        self.e2_targets = self.__calc_targets(
            spread_opp.e2_spread, self.h_to_e2_max, self.trader1.quote_bal)

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
        self.e1_targets = self.__calc_targets(
            spread_opp.e1_spread, self.h_to_e1_max, self.trader2.quote_bal)

    def __evaluate_spread(self, spread_opp):
        """Evaluate spread numbers against targets and set up state for
        trade execution.

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

        # NOTE: Trader's `quote_target_amount` is updated here.
        buy_trader.quote_target_amount = min(trade_vol, buy_trader.quote_bal)

        if buy_trader is self.trader1:
            buy_price = spread_opp.e1_buy
            sell_price = spread_opp.e2_sell
        else:
            buy_price = spread_opp.e2_buy
            sell_price = spread_opp.e1_sell

        self.trade_metadata = {
            'buy_price': buy_price,
            'sell_price': sell_price,
            'buy_trader': buy_trader,
            'sell_trader': sell_trader
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
        if self.config[DRYRUN]:
            logging.info("**Dry run - begin fake execution")
            executed_amount = arbseeker.execute_buy(
                self.trade_metadata['buy_trader'],
                self.trade_metadata['buy_price'])
            arbseeker.execute_sell(
                self.trade_metadata['sell_trader'],
                self.trade_metadata['sell_price'],
                executed_amount)
            logging.info("**Dry run - end fake execution")
        else:
            try:
                buy_response = arbseeker.execute_buy(
                    self.trade_metadata['buy_trader'],
                    self.trade_metadata['buy_price'])
                executed_amount = buy_response['post_fee_base']
                # TODO: Persist into database.
            except Exception as exc:
                logging.error(exc, exc_info=True)
                self.checkpoint.restore(self)
            else:
                # If an exception is thrown, we want the program to stop on the
                # second trade.
                try:
                    sell_response = arbseeker.execute_sell(
                        self.trade_metadata['sell_trader'],
                        self.trade_metadata['sell_price'],
                        executed_amount)

                    if executed_amount != sell_response['pre_fee_base']:
                        msg = ("The purchased base amount does not match with "
                               "the sold amount. Normal execution has "
                               "terminated.\nBought amount: {}\n, Sold amount:"
                               " {}").format(
                                    executed_amount,
                                    sell_response['pre_fee_base'])

                        raise IncompleteArbitrageError(msg)
                    else:
                        # TODO: Persist into database.
                        pass
                except Exception as exc:
                    self._send_email("TRADE ERROR ALERT", repr(exc))
                    logging.error(exc, exc_info=True)
                    # TODO: Update to start dryrun bot if irrecoverable error occurs.
                    raise
                else:
                    # Retrieve updated wallet balances if everything worked
                    # as expected.
                    self.trader1.fetch_wallet_balances()
                    self.trader2.fetch_wallet_balances()

    def _poll_opportunity(self):
        """Poll exchanges for arbitrage opportunity.

        Returns:
            bool: Whether there is an opportunity.
        """
        # Set quote target amount based on strategy.
        self.trader1.quote_target_amount = max(self.vol_min, self.trader1.quote_bal)
        self.trader2.quote_target_amount = max(self.vol_min, self.trader2.quote_bal)

        try:
            spread_opp = arbseeker.get_spreads_by_ob(
                self.trader1, self.trader2)
        except ccxt.NetworkError as network_error:
            logging.error(network_error, exc_info=True)
            return False

        is_opportunity = False

        if not self.has_started:
            self.momentum = Momentum.NEUTRAL

            self.e1_targets = self.__calc_targets(spread_opp.e1_spread,
                self.h_to_e1_max, self.trader2.quote_bal)
            self.e2_targets = self.__calc_targets(spread_opp.e2_spread,
                self.h_to_e2_max, self.trader1.quote_bal)

            self.target_index = 0
            self.last_target_index = 0
            self.has_started = True
        else:
            # Save the autotrageur state before proceeding with algorithm.
            self.checkpoint.save(self)
            is_opportunity = self.__evaluate_spread(spread_opp)

        self.h_to_e1_max = max(self.h_to_e1_max, spread_opp.e1_spread)
        self.h_to_e2_max = max(self.h_to_e2_max, spread_opp.e2_spread)

        return is_opportunity

    def _send_email(self, subject, msg):
        """Send email alert to preconfigured emails.

        Args:
            subject (str): The subject of the message
            msg (str): The contents of the email to send out.
        """
        send_all_emails(self.config[EMAIL_CFG_PATH],
                        'Subject: {}\n{}'.format(subject, msg))

    # @Override
    def _setup(self):
        """Sets up the algorithm to use.

        Raises:
            AuthenticationError: If not dryrun and authentication fails.
        """
        super()._setup()
        self.spread_min = num_to_decimal(self.config[SPREAD_MIN])
        self.vol_min = num_to_decimal(self.config[VOL_MIN])
        self.h_to_e1_max = num_to_decimal(self.config[H_TO_E1_MAX])
        self.h_to_e2_max = num_to_decimal(self.config[H_TO_E2_MAX])
        self.checkpoint = FCFCheckpoint()
