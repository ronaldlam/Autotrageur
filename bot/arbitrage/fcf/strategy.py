import logging
from collections import namedtuple

import ccxt

import bot.arbitrage.arbseeker as arbseeker
from bot.arbitrage.fcf.target_tracker import FCFTargetTracker
from bot.arbitrage.fcf.trade_chunker import FCFTradeChunker
from bot.common.enums import Momentum
from bot.trader.ccxt_trader import OrderbookException
from fp_libs.constants.decimal_constants import ONE
from fp_libs.utilities import num_to_decimal


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


class FCFStrategyState():
    """Holds the state of the FCFStrategy."""

    def __init__(self, has_started, h_to_e1_max, h_to_e2_max):
        """Constructor.

        Args:
            has_started (bool): Whether the algorithm is past its first
                poll.
            h_to_e1_max (Decimal): The historical max spread trading e2
                to e1.
            h_to_e2_max (Decimal): The historical max spread trading e1
                to e2.
        """
        self.has_started = has_started
        self.h_to_e1_max = h_to_e1_max
        self.h_to_e2_max = h_to_e2_max
        self.momentum = None
        self.e1_targets = None
        self.e2_targets = None
        self.target_tracker = None
        self.trade_chunker = None

    def __repr__(self):
        """Printable representation of the Configuration, for debugging."""
        return ("Entire Strategy State: {}\nTarget Tracker: {}\n Trade Chunker:"
                " {}\n".format(
                    str(self.__dict__),
                    self.target_tracker.__dict__,
                    self.trade_chunker.__dict__))


class FCFStrategyBuilder():
    """Builder for the FCFStrategy class."""

    def set_h_to_e1_max(self, h_to_e1_max):
        """Set the h_to_e1_max of the builder.

        Args:
            h_to_e1_max (Decimal): The historical max spread to e1.

        Returns:
            FCFStrategyBuilder: The current FCFStrategyBuilder.
        """
        self.h_to_e1_max = h_to_e1_max
        return self

    def set_h_to_e2_max(self, h_to_e2_max):
        """Set the h_to_e2_max of the builder.

        Args:
            h_to_e2_max (Decimal): The historical max spread to e2.

        Returns:
            FCFStrategyBuilder: The current FCFStrategyBuilder.
        """
        self.h_to_e2_max = h_to_e2_max
        return self

    def set_has_started(self, has_started):
        """Set the has_started of the builder.

        Args:
            has_started (bool): Whether the first poll has completed.

        Returns:
            FCFStrategyBuilder: The current FCFStrategyBuilder.
        """
        self.has_started = has_started
        return self

    def set_max_trade_size(self, max_trade_size):
        """Set the max_trade_size of the builder.

        Args:
            max_trade_size (Decimal): The maximum USD value per trade.

        Returns:
            FCFStrategyBuilder: The current FCFStrategyBuilder.
        """
        self.max_trade_size = max_trade_size
        return self

    def set_spread_min(self, spread_min):
        """Set the spread_min of the builder.

        Args:
            spread_min (Decimal): The minimum spread used for
                calculating trade targets.

        Returns:
            FCFStrategyBuilder: The current FCFStrategyBuilder.
        """
        self.spread_min = spread_min
        return self

    def set_vol_min(self, vol_min):
        """Set the vol_min of the builder.

        Args:
            vol_min (Decimal): The minimum volume of the first trade for
                trade target calculation.

        Returns:
            FCFStrategyBuilder: The current FCFStrategyBuilder.
        """
        self.vol_min = vol_min
        return self

    def set_manager(self, autotrageur):
        """Set the autotrageur manager of the builder.

        Args:
            autotrageur (Autotrageur): The Autotrageur object which the
                Strategy will use for communication with other components.

        Returns:
            FCFStrategyBuilder: The builder with its built parts so far.
        """
        self.manager = autotrageur
        return self

    def build(self):
        """Return the FCFStrategy with the set attributes.

        NOTE: We get the nice AttributeError if something is unset.

        Returns:
            FCFStrategy: The constructed FCFStrategy.
        """
        return FCFStrategy(
            FCFStrategyState(
                self.has_started,
                self.h_to_e1_max,
                self.h_to_e2_max),
            self.manager,
            self.max_trade_size,
            self.spread_min,
            self.vol_min)


class FCFStrategy():
    """Class containing the core strategy for the FCFAutotrageur."""

    def __init__(self, strategy_state, manager, max_trade_size, spread_min,
                 vol_min):
        """Constructor.

        Args:
            strategy_state (FCFStrategyState): Helper object that stores
                current algorithm state.
            manager (Autotrageur): The Autotrageur object which the
                Strategy will use for communication with other components.
            max_trade_size (Decimal): The maximum USD value that the bot
                will attempt to arbitrage in a single trade.
            spread_min (Decimal): The minimum spread increment between
                trades.
            vol_min (Decimal): The ideal minimum volume the algorithm
                uses to calculate targets.
        """
        self.state = strategy_state
        self._manager = manager
        self._spread_min = spread_min
        self._vol_min = vol_min
        self._max_trade_size = max_trade_size

        self.target_tracker = FCFTargetTracker()
        self.trade_chunker = FCFTradeChunker(max_trade_size)

        # Save any stateful objects to the Strategy State.
        self.state.target_tracker = self.target_tracker
        self.state.trade_chunker = self.trade_chunker

    @property
    def spread_min(self):
        """Property getter for the strategy's spread_min.

        Returns:
            Decimal: The strategy's spread_min.
        """
        return self._spread_min

    @spread_min.setter
    def spread_min(self, spread_min):
        """Property setter for the strategy's spread_min.

        Args:
            spread_min (Decimal): A spread_min to set.

        Raises:
            AttributeError: Raised if a spread_min has already been set.  It
                should not change during an FCF run.
        """
        if hasattr(self, '_spread_min'):
            raise AttributeError("spread_min cannot be changed during an FCF "
                "run")
        self._spread_min = spread_min

    @property
    def vol_min(self):
        """Property getter for the strategy's vol_min.

        Returns:
            Decimal: The strategy's vol_min.
        """
        return self._vol_min

    @vol_min.setter
    def vol_min(self, vol_min):
        """Property setter for the strategy's vol_min.

        Args:
            vol_min (Decimal): A vol_min to set.

        Raises:
            AttributeError: Raised if a vol_min has already been set.  It
                should not change during an FCF run.
        """
        if hasattr(self, '_vol_min'):
            raise AttributeError("vol_min cannot be changed during an FCF "
                "run")
        self._vol_min = vol_min

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
        return buy_trader.quote_target_amount > self.__get_min_target_amount()

    def __evaluate_to_e1_trade(self, momentum_change, spread_opp):
        """Changes state information to prepare for the trades from e2
        to e1.

        Args:
            momentum_change (bool): Whether there was a momentum change.
            spread_opp (SpreadOpportunity): The spread and price info.
        """
        self.target_tracker.advance_target_index(
            spread_opp.e1_spread, self.state.e1_targets)
        self.__prepare_trade(
            momentum_change,
            self._manager.trader2,
            self._manager.trader1,
            self.state.e1_targets,
            spread_opp)

    def __evaluate_to_e2_trade(self, momentum_change, spread_opp):
        """Changes state information to prepare for the trades from e1
        to e2.

        Args:
            momentum_change (bool): Whether there was a momentum change.
            spread_opp (SpreadOpportunity): The spread and price info.
        """
        self.target_tracker.advance_target_index(
            spread_opp.e2_spread, self.state.e2_targets)
        self.__prepare_trade(
            momentum_change,
            self._manager.trader1,
            self._manager.trader2,
            self.state.e2_targets,
            spread_opp)

    def __get_min_target_amount(self):
        """Fetch the minimum target amount that the exchanges support.

        Should be used only when trade_metadata is set and there is a
        potential trade. The result is based on the buy price.

        Returns:
            Decimal: The minimum target amount in quote currency.
        """
        min_base_buy = self.trade_metadata.buy_trader.get_min_base_limit()
        min_base_sell = self.trade_metadata.sell_trader.get_min_base_limit()
        return self.trade_metadata.buy_price * max(min_base_buy, min_base_sell)

    def __is_trade_opportunity(self, spread_opp):
        """Evaluate spread numbers against targets and set up state for
        trade execution.

        Args:
            spread_opp (SpreadOpportunity): The spread and price info.

        Returns:
            bool: Whether there is a trade opportunity.
        """
        state = self.state
        if state.momentum is Momentum.NEUTRAL:
            if self.target_tracker.has_hit_targets(
                    spread_opp.e2_spread, state.e2_targets, True):
                self.__evaluate_to_e2_trade(True, spread_opp)
                state.momentum = Momentum.TO_E2
                return True
            elif self.target_tracker.has_hit_targets(
                    spread_opp.e1_spread, state.e1_targets, True):
                self.__evaluate_to_e1_trade(True, spread_opp)
                state.momentum = Momentum.TO_E1
                return True
        elif state.momentum is Momentum.TO_E2:
            if self.target_tracker.has_hit_targets(
                    spread_opp.e2_spread, state.e2_targets, False):
                self.__evaluate_to_e2_trade(False, spread_opp)
                return True
            # Momentum change from TO_E2 to TO_E1.
            elif self.target_tracker.has_hit_targets(
                    spread_opp.e1_spread, state.e1_targets, True):
                self.target_tracker.reset_target_index()
                logging.debug('#### Momentum changed from TO_E2 to TO_E1')
                logging.debug('#### TO_E1 spread: {} > First TO_E1 target {}'.
                              format(
                                  spread_opp.e1_spread,
                                  state.e1_targets[0][0]))
                self.__evaluate_to_e1_trade(True, spread_opp)
                state.momentum = Momentum.TO_E1
                return True
        elif state.momentum is Momentum.TO_E1:
            # Momentum change from TO_E1 to TO_E2.
            if self.target_tracker.has_hit_targets(
                    spread_opp.e2_spread, state.e2_targets, True):
                self.target_tracker.reset_target_index()
                logging.debug('#### Momentum changed from TO_E1 to TO_E2')
                logging.debug('#### TO_E2 spread: {} > First TO_E2 target {}'.
                              format(
                                  spread_opp.e2_spread,
                                  state.e2_targets[0][0]))
                self.__evaluate_to_e2_trade(True, spread_opp)
                state.momentum = Momentum.TO_E2
                return True
            elif self.target_tracker.has_hit_targets(
                    spread_opp.e1_spread, state.e1_targets, False):
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
        # Note that both target tracker and trade chunker use USD internally.
        total_usd_vol = self.target_tracker.get_trade_volume(
            targets, is_momentum_change)

        if is_momentum_change or self.trade_chunker.trade_completed:
            self.trade_chunker.reset(total_usd_vol)

        next_usd_vol = self.trade_chunker.get_next_trade()
        next_quote_vol = buy_trader.get_quote_from_usd(next_usd_vol)

        # NOTE: Trader's `quote_target_amount` is updated here.  We need to use
        # the quote balance in case of intra-day forex fluctuations which
        # would result in an inaccurate USD balance.
        target_quote_amount = min(
            next_quote_vol, buy_trader.adjusted_quote_bal)
        buy_trader.set_buy_target_amount(target_quote_amount, is_usd=False)

        if buy_trader is self._manager.trader1:
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

    def __update_trade_targets(self):
        """Updates the trade targets based on the direction of the completed
        trade.  E.g. If the trade was performed from e1 -> e2, then the
        `e1_targets` should be updated, vice versa.

        NOTE: Trade targets should only be updated if a trade was completely
        successful (buy and sell trades completed).
        """
        if self.trade_metadata.buy_trader is self._manager.trader2:
            self.state.e2_targets = self.__calc_targets(
                self.trade_metadata.spread_opp.e2_spread,
                self.state.h_to_e2_max,
                self._manager.trader1.get_adjusted_usd_balance())
            logging.debug("#### New calculated e2_targets: {}".format(
                list(enumerate(self.state.e2_targets))))
        else:
            self.state.e1_targets = self.__calc_targets(
                self.trade_metadata.spread_opp.e1_spread,
                self.state.h_to_e1_max,
                self._manager.trader2.get_adjusted_usd_balance())
            logging.debug("#### New calculated e1_targets: {}".format(
                list(enumerate(self.state.e1_targets))))

    def clean_up(self):
        """Clean up any state information before the next poll."""
        self.trade_metadata = None

    def finalize_trade(self, buy_response, sell_response):
        """After an executed trade, updates any state to reflect the completed
        trade.

        NOTE: The strategy interface takes the whole responses for
        processing in case any state within the algorithm needs to
        change after the trade is made. In this implementation, only the
        buy_response is used.

        Args:
            buy_response (dict): The Autotrageur specific unified buy
                response.
            sell_response (dict): The Autotrageur specific unified
                sell response.
        """
        # Feed real trade data to chunker to calculate next trade size.
        post_fee_usd = self.trade_metadata.buy_trader.get_usd_from_quote(
            buy_response['post_fee_quote'])
        min_usd_trade_size = self.trade_metadata.buy_trader.get_usd_from_quote(
            self.__get_min_target_amount())
        self.trade_chunker.finalize_trade(post_fee_usd, min_usd_trade_size)

        # We increment the target index only after the chunks completely make
        # up the target.
        if self.trade_chunker.trade_completed:
            self.target_tracker.increment()

        # Retrieve updated wallet balances if everything worked
        # as expected.
        self._manager.trader1.update_wallet_balances()
        self._manager.trader2.update_wallet_balances()

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
        trader1_balance = self._manager.trader1.get_adjusted_usd_balance()
        trader2_balance = self._manager.trader2.get_adjusted_usd_balance()

        trader1_buy_target_amount = min(
            self._max_trade_size,
            max(self.vol_min, trader1_balance))
        trader2_buy_target_amount = min(
            self._max_trade_size,
            max(self.vol_min,trader2_balance))

        self._manager.trader1.set_buy_target_amount(trader1_buy_target_amount)
        self._manager.trader1.set_rough_sell_amount(trader2_buy_target_amount)
        self._manager.trader2.set_buy_target_amount(trader2_buy_target_amount)
        self._manager.trader2.set_rough_sell_amount(trader1_buy_target_amount)

        try:
            spread_opp = arbseeker.get_spreads_by_ob(
                self._manager.trader1, self._manager.trader2)
        except (ccxt.NetworkError, OrderbookException) as exc:
            logging.error(exc, exc_info=True)
            return False

        self._manager.balance_checker.check_crypto_balances(spread_opp)

        is_opportunity = False

        if not self.state.has_started:
            self.state.momentum = Momentum.NEUTRAL

            self.state.e1_targets = self.__calc_targets(
                spread_opp.e1_spread, self.state.h_to_e1_max,
                self._manager.trader2.get_adjusted_usd_balance())
            logging.debug('#### Initial e1_targets: {}'.format(
                list(enumerate(self.state.e1_targets))))
            self.state.e2_targets = self.__calc_targets(
                spread_opp.e2_spread, self.state.h_to_e2_max,
                self._manager.trader1.get_adjusted_usd_balance())
            logging.debug('#### Initial e2_targets: {}'.format(
                list(enumerate(self.state.e2_targets))))

            self.state.has_started = True

            # Need to save the strategy state even after first poll to ensure
            # resume behaviour works correctly.
            self._manager.checkpoint.strategy_state = self.state
            self.has_started = True
        else:
            # Save the autotrageur state before proceeding with next algorithm
            # cycle.
            self._manager.checkpoint.strategy_state = self.state
            if self.__is_trade_opportunity(spread_opp):
                logging.debug('#### Is a trade opportunity')
                is_opportunity = self.__check_within_limits()
                if not is_opportunity:
                    # Targets were hit, but current balances cannot facilitate
                    # trade. Recalculate targets with no balance update.
                    self.__update_trade_targets()
                    # If the trade is not within the exchange limits, there is
                    # no longer a way to complete the trade at the current
                    # target. We mark the trade complete to reset the polling
                    # interval.
                    self.trade_chunker.trade_completed = True
                logging.debug(
                    '#### Is within exchange limits: {}'.format(is_opportunity))

        self.state.h_to_e1_max = max(
            self.state.h_to_e1_max, spread_opp.e1_spread)
        self.state.h_to_e2_max = max(
            self.state.h_to_e2_max, spread_opp.e2_spread)

        return is_opportunity
