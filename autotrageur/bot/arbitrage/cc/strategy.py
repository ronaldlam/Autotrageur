from autotrageur.bot.arbitrage.trade_chunker import TradeChunker


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

    def poll_opportunity(self):
        """Poll exchanges for arbitrage opportunity.

        Returns:
            bool: Whether there is an opportunity.
        """
        # Set trader target amounts based on strategy.
        trader1_balance = self._manager.trader1.get_adjusted_usd_balance()
        trader2_balance = self._manager.trader2.get_adjusted_usd_balance()

        trader1_buy_target_amount = min(self._max_trade_size, trader1_balance)
        trader2_buy_target_amount = min(self._max_trade_size, trader2_balance)

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
