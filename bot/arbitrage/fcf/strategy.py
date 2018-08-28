import logging
from collections import namedtuple

import ccxt

import bot.arbitrage.arbseeker as arbseeker
from bot.common.enums import Momentum
from bot.trader.ccxt_trader import OrderbookException
from libs.constants.decimal_constants import ONE
from libs.utilities import num_to_decimal


# See https://stackoverflow.com/questions/1606436/adding-docstrings-to-namedtuples
class TradeMetadata(namedtuple('TradeMetadata', [
        'spread_opp', 'buy_price', 'sell_price', 'buy_trader', 'sell_trader'])):
    """Encapsulates trade metadata produced by algorithm for execution.

    Args:
        spread_opp (SpreadOpportunity): The spread opportunity to
            consider.
        buy_price (Decimal): The buy price.
        sell_price (Decimal): The sell price.
        buy_trader (CCXTTrader): The trader for the buy side exchange.
        sell_trader (CCXTTrader): The trader for the sell side exchange.
    """
    __slots__ = ()


class InsufficientCryptoBalance(Exception):
    """Thrown when there is not enough crypto balance to fulfill the matching
    sell order."""
    pass


class FCFStrategyBuilder():
    """Builder for the FCFStrategy class."""

    def set_h_to_e1_max(self, h_to_e1_max):
        """Set the h_to_e1_max of the builder."""
        self.h_to_e1_max = h_to_e1_max
        return self

    def set_h_to_e2_max(self, h_to_e2_max):
        """Set the h_to_e2_max of the builder."""
        self.h_to_e2_max = h_to_e2_max
        return self

    def set_has_started(self, has_started):
        """Set the has_started of the builder."""
        self.has_started = has_started
        return self

    def set_spread_min(self, spread_min):
        """Set the spread_min of the builder."""
        self.spread_min = spread_min
        return self

    def set_vol_min(self, vol_min):
        """Set the vol_min of the builder."""
        self.vol_min = vol_min
        return self

    def set_balance_checker(self, balance_checker):
        """Set the balance_checker of the builder."""
        self.balance_checker = balance_checker
        return self

    def set_checkpoint(self, checkpoint):
        """Set the checkpoint of the builder."""
        self.checkpoint = checkpoint
        return self

    def set_trader1(self, trader1):
        """Set the trader1 of the builder."""
        self.trader1 = trader1
        return self

    def set_trader2(self, trader2):
        """Set the trader2 of the builder."""
        self.trader2 = trader2
        return self

    def build(self):
        """Return the FCFStrategy with the set attributes.

        NOTE: We get the nice AttributeError if something is unset.

        Returns:
            FCFStrategy: The constructed FCFStrategy.
        """
        return FCFStrategy(
            self.h_to_e1_max, self.h_to_e2_max, self.has_started,
            self.spread_min, self.vol_min, self.balance_checker,
            self.checkpoint, self.trader1, self.trader2)


class FCFStrategy():
    """Class containing the core strategy for the FCFAutotrageur."""

    def __init__(self, h_to_e1_max, h_to_e2_max, has_started, spread_min,
                 vol_min, balance_checker, checkpoint, trader1, trader2):
        """Constructor.

        Args:
            h_to_e1_max (Decimal): The historical max spread trading e1
                to e2.
            h_to_e2_max (Decimal): The historical max spread trading e2
                to e1.
            has_started (bool): Whether the algorithm is past its first
                poll.
            spread_min (Decimal): The minimum spread increment between
                trades.
            vol_min (Decimal): The ideal minimum volume the algorithm
                uses to calculate targets.
            balance_checker (FCFBalanceChecker): Helper object to
                determine whether crypto balances are sufficient.
            checkpoint (FCFCheckpoint): Helper object that stores
                current algorithm state.
            trader1 (CCXTTrader): The trader for the first exchange.
            trader2 (CCXTTrader): The trader for the second exchange.
        """
        self.h_to_e1_max = h_to_e1_max
        self.h_to_e2_max = h_to_e2_max
        self.has_started = has_started
        self.spread_min = spread_min
        self.vol_min = vol_min
        self.balance_checker = balance_checker
        self.checkpoint = checkpoint
        self.trader1 = trader1
        self.trader2 = trader2

    def __advance_target_index(self, spread, targets):
        """Increment the target index to minimum target greater than
        spread.

        Args:
            spread (Decimal): The calculated spread.
            targets (list): The list of targets.
        """
        while (self.target_index + 1 < len(targets) and
                spread >= targets[self.target_index + 1][0]):
            logging.debug(
                '#### target_index before: {}'.format(self.target_index))
            self.target_index += 1
            logging.debug(
                '#### target_index after: {}'.format(self.target_index))

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

    def __check_within_limits(self):
        """Check whether potential trade meets minimum volume limits.

        Should be used only when trade_metadata is set and there is a
        potential trade.

        Returns:
            bool: Whether the trade falls within the limits.
        """
        buy_trader = self.trade_metadata.buy_trader
        sell_trader = self.trade_metadata.sell_trader
        min_base_buy = buy_trader.get_min_base_limit()
        min_base_sell = sell_trader.get_min_base_limit()
        min_target_amount = (self.trade_metadata.buy_price
                             * max(min_base_buy, min_base_sell))
        return buy_trader.quote_target_amount > min_target_amount

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
                logging.debug('#### TO_E1 spread: {} > First TO_E1 target {}'.
                              format(spread_opp.e1_spread, self.e1_targets[0][0]))
                self.__evaluate_to_e1_trade(True, spread_opp)
                self.momentum = Momentum.TO_E1
                return True
        elif self.momentum is Momentum.TO_E1:
            # Momentum change from TO_E1 to TO_E2.
            if spread_opp.e2_spread >= self.e2_targets[0][0]:
                self.target_index = 0
                logging.debug('#### Momentum changed from TO_E1 to TO_E2')
                logging.debug('#### TO_E2 spread: {} > First TO_E2 target {}'.
                              format(spread_opp.e2_spread, self.e2_targets[0][0]))
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

        self.trade_metadata = TradeMetadata(
            spread_opp=spread_opp,
            buy_price=buy_price,
            sell_price=sell_price,
            buy_trader=buy_trader,
            sell_trader=sell_trader
        )

        required_base = (
            buy_trader.quote_target_amount / self.trade_metadata.buy_price)
        base = buy_trader.base

        if required_base > sell_trader.base_bal:
            exc_msg = ("Insufficient crypto balance on: {exchange}.\n"
                       "Required base: {req_base} {base}\n"
                       "Actual base: {act_base} {base}")
            raise InsufficientCryptoBalance(
                exc_msg.format(
                    exchange=sell_trader.exchange_name,
                    req_base=required_base,
                    act_base=sell_trader.base_bal,
                    base=base))

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
        if self.trade_metadata.buy_trader is self.trader2:
            self.e2_targets = self.__calc_targets(
                self.trade_metadata.spread_opp.e2_spread, self.h_to_e2_max,
                self.trader1.get_usd_balance())
            logging.debug("#### New calculated e2_targets: {}".format(
                list(enumerate(self.e2_targets))))
        else:
            self.e1_targets = self.__calc_targets(
                self.trade_metadata.spread_opp.e1_spread, self.h_to_e1_max,
                self.trader2.get_usd_balance())
            logging.debug("#### New calculated e1_targets: {}".format(
                list(enumerate(self.e1_targets))))

    def clean_up(self):
        """Clean up any state information before the next poll."""
        self.trade_metadata = None

    def restore(self):
        """Rollback to previous saved state."""
        self.checkpoint.restore(self)

    def finalize_trade(self):
        """Do cleanup after trade is executed."""
        # Retrieve updated wallet balances if everything worked
        # as expected.
        self.trader1.update_wallet_balances()
        self.trader2.update_wallet_balances()

        # Calculate the targets after the potential trade so that the wallet
        # balances are the most up to date for the target amounts.
        self.__update_trade_targets()

    def get_trade_data(self):
        """Get trade metadata.

        Returns:
            TradeMetadata: The trade metadata to execute on.
        """
        return self.trade_metadata

    def poll_opportunity(self):
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

        self.balance_checker.check_crypto_balances(spread_opp)

        is_opportunity = False

        if not self.has_started:
            self.momentum = Momentum.NEUTRAL

            self.e1_targets = self.__calc_targets(
                spread_opp.e1_spread, self.h_to_e1_max,
                self.trader2.get_usd_balance())
            logging.debug('#### Initial e1_targets: {}'.format(
                list(enumerate(self.e1_targets))))
            self.e2_targets = self.__calc_targets(
                spread_opp.e2_spread, self.h_to_e2_max,
                self.trader1.get_usd_balance())
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
                if not is_opportunity:
                    # Targets were hit, but current balances cannot facilitate
                    # trade. Recalculate targets with no balance update.
                    self.__update_trade_targets()
                logging.debug(
                    '#### Is within exchange limits: {}'.format(is_opportunity))

        self.h_to_e1_max = max(self.h_to_e1_max, spread_opp.e1_spread)
        self.h_to_e2_max = max(self.h_to_e2_max, spread_opp.e2_spread)

        return is_opportunity
