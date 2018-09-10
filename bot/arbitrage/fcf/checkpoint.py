from bot.arbitrage.autotrageur import Configuration
from bot.arbitrage.fcf.strategy import FCFStrategyState
from bot.trader.dry_run import DryRunManager


class FCFCheckpoint():
    """Contains the current autotrageur state.

    Encapsulates values pertaining to the autotrageur run.  Useful for rollback
    situations.
    """

    def __init__(self, config):
        """Constructor.

        Initializes all state-related objects and variables.  Persists the
        bot's configuration right upon initialization while the others are
        set when required.

        Args:
            config (Configuration): The current Configuration of the bot.
        """
        self._config = config

    @property
    def config(self):
        """Property getter for the checkpoint's config.

        Returns:
            Configuration: The checkpoint's saved config.
        """
        return self._config

    @config.setter
    def config(self, config):
        """Property setter for the checkpoint's config.

        Args:
            config (Configuration): A configuration to save into the checkpoint.

        Raises:
            TypeError: Raised if not type Configuration.
            AttributeError: Raised if a Configuration has already been saved
                in the checkpoint - ensuring that the config is not
                accidentally overwritten.
        """
        if not isinstance(config, Configuration):
            raise TypeError("config must be of type Configuration.")
        if hasattr(self, '_config'):
            raise AttributeError("a Configuration cannot be changed during a "
                "run")
        self._config = config

    @property
    def dry_run_manager(self):
        """Property getter for the checkpoint's dry run manager.

        Returns:
            DryRunManager: The checkpoint's saved dry run manager.
        """
        return self._dry_run_manager

    @dry_run_manager.setter
    def dry_run_manager(self, dry_run_manager):
        """Property setter for the checkpoint's dry run manager.

        Args:
            dry_run_manager (DryRunManager): A dry run manager to save into the
                checkpoint.

        Raises:
            TypeError: Raised if not type DryRunManager.
        """
        if not isinstance(dry_run_manager, DryRunManager):
            raise TypeError("a dry run manager must be of type DryRunManager.")
        self._dry_run_manager = dry_run_manager

    @property
    def strategy_state(self):
        """Property getter for the checkpoint's strategy state.

        Returns:
            FCFStrategyState: The checkpoint's saved strategy state.
        """
        return self._strategy_state

    @strategy_state.setter
    def strategy_state(self, strategy_state):
        """Property setter for the checkpoint's strategy state.

        Args:
            strategy_state (FCFStrategyState): A strategy state to save into the
                checkpoint.

        Raises:
            TypeError: Raised if not type FCFStrategyState.
        """
        if not isinstance(strategy_state, FCFStrategyState):
            raise TypeError("strategy state must be of type FCFStrategyState.")
        self._strategy_state = strategy_state

    def __repr__(self):
        """Printable representation of the FCFCheckpoint, for debugging."""
        return "FCFCheckpoint state objects:\n{0!r}\n{1!r}\n{2!r}".format(
            self.config, self.strategy_state, self.dry_run_manager)
