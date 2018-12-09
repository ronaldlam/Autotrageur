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
