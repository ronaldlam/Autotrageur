import logging

import ccxt

import autotrageur.bot.arbitrage.arbseeker as arbseeker
from autotrageur.bot.arbitrage.trade_chunker import TradeChunker
from autotrageur.bot.trader.ccxt_trader import OrderbookException


class CCStrategyState():
    """Reserved for future use."""
    pass


class CCStrategyBuilder():
    """Builder for the CCStrategy class."""

    def set_max_trade_size(self, max_trade_size):
        """Set the max_trade_size of the builder.

        Args:
            max_trade_size (Decimal): The maximum USD value per trade.

        Returns:
            CCStrategyBuilder: The current CCStrategyBuilder.
        """
        self.max_trade_size = max_trade_size
        return self

    def set_spread_min(self, spread_min):
        """Set the spread_min of the builder.

        Args:
            spread_min (Decimal): The minimum spread used for
                calculating trade targets.

        Returns:
            CCStrategyBuilder: The current CCStrategyBuilder.
        """
        self.spread_min = spread_min
        return self

    def set_manager(self, autotrageur):
        """Set the autotrageur manager of the builder.

        Args:
            autotrageur (Autotrageur): The Autotrageur object which the
                Strategy will use for communication with other components.

        Returns:
            CCStrategyBuilder: The builder with its built parts so far.
        """
        self.manager = autotrageur
        return self

    def build(self):
        """Return the CCStrategy with the set attributes.

        NOTE: We get the nice AttributeError if something is unset.

        Returns:
            CCStrategy: The constructed CCStrategy.
        """
        return CCStrategy(
            CCStrategyState(),
            self.manager,
            self.max_trade_size,
            self.spread_min)


class CCStrategy():
    """Class containing the core strategy for the CCAutotrageur."""

    def __init__(self, strategy_state, manager, max_trade_size, spread_min):
        """Constructor.

        Args:
            strategy_state (CCStrategyState): Helper object that stores
                current algorithm state.
            manager (Autotrageur): The Autotrageur object which the
                Strategy will use for communication with other components.
            max_trade_size (Decimal): The maximum USD value that the bot
                will attempt to arbitrage in a single trade.
            spread_min (Decimal): The minimum spread increment between
                trades.
        """
        self.state = strategy_state
        self._manager = manager
        self._spread_min = spread_min
        self._max_trade_size = max_trade_size

        self.trade_chunker = TradeChunker(max_trade_size)

        # Save any stateful objects to the Strategy State.
        self.state.trade_chunker = self.trade_chunker

    def __check_within_limits(self):
        """Check whether potential trade meets minimum volume limits.

        Should be used only when trade_metadata is set and there is a
        potential trade.

        Returns:
            bool: Whether the trade falls within the limits.
        """
        buy_trader = self.trade_metadata.buy_trader
        return buy_trader.quote_target_amount > self.__get_min_target_amount()

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
            # TODO: Now we need to initiate withdrawal.
            pass

        # Retrieve updated wallet balances if everything worked
        # as expected.
        self._manager.trader1.update_wallet_balances()
        self._manager.trader2.update_wallet_balances()

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
        t1 = self._manager.trader1
        t2 = self._manager.trader2

        trader1_balance = t1.adjusted_quote_bal
        trader2_balance = t2.adjusted_quote_bal

        # We are using quote balances here.
        t1_buy_target = min(self._max_trade_size, trader1_balance)
        t2_buy_target = min(self._max_trade_size, trader2_balance)

        t1.set_buy_target_amount(t1_buy_target, False)
        t1.set_rough_sell_amount(t2_buy_target, False)
        t2.set_buy_target_amount(t2_buy_target, False)
        t2.set_rough_sell_amount(t1_buy_target, False)

        try:
            spread_opp = arbseeker.get_spreads_by_ob(t1, t2)
        except (ccxt.NetworkError, OrderbookException) as exc:
            logging.error(exc, exc_info=True)
            return False

        # Ding ding! We want to trade.
        if spread_opp.e1_spread >= self._spread_min:
            # The corrected_buy_target represents calculation based on pricing
            # of the current poll.
            base_limited_buy_target = t1.base_bal * spread_opp.e2_buy
            corrected_buy_target = min(t2_buy_target, base_limited_buy_target)

            if self.trade_chunker.trade_completed:
                self.trade_chunker.reset(corrected_buy_target)

            # The chunked_target represents calculations based on pricing of
            # the first poll that reset the chunker. We require this to hold
            # 'trade state' that increases polling rate. Future work can
            # dynamically change the target stored in the chunker.
            chunked_target = self.trade_chunker.get_next_trade()
            next_target = min(corrected_buy_target, chunked_target)

            t2.set_buy_target_amount(next_target, False)
            self.trade_metadata = arbseeker.TradeMetadata(
                spread_opp=spread_opp,
                buy_price=spread_opp.e2_buy,
                sell_price=spread_opp.e1_sell,
                buy_trader=t2,
                sell_trader=t1)

            if self.__check_within_limits():
                return True
            else:
                self.trade_chunker.trade_completed = True
                # TODO: Initiate withdrawal
        elif spread_opp.e2_spread >= self._spread_min:
            # The corrected_buy_target represents calculation based on pricing
            # of the current poll.
            base_limited_buy_target = t2.base_bal * spread_opp.e1_buy
            corrected_buy_target = min(t1_buy_target, base_limited_buy_target)

            if self.trade_chunker.trade_completed:
                self.trade_chunker.reset(corrected_buy_target)

            # The chunked_target represents calculations based on pricing of
            # the first poll that reset the chunker. We require this to hold
            # 'trade state' that increases polling rate. Future work can
            # dynamically change the target stored in the chunker.
            chunked_target = self.trade_chunker.get_next_trade()
            next_target = min(corrected_buy_target, chunked_target)

            t1.set_buy_target_amount(next_target, False)
            self.trade_metadata = arbseeker.TradeMetadata(
                spread_opp=spread_opp,
                buy_price=spread_opp.e1_buy,
                sell_price=spread_opp.e2_sell,
                buy_trader=t1,
                sell_trader=t2)

            if self.__check_within_limits():
                return True
            else:
                self.trade_chunker.trade_completed = True
                # TODO: Initiate withdrawal

        return False
