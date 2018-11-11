from autotrageur.bot.arbitrage.autotrageur import Configuration
from autotrageur.bot.arbitrage.fcf.strategy import FCFStrategyState
from autotrageur.bot.arbitrage.fcf.fcf_stat_tracker import FCFStatTracker
from autotrageur.version import VERSION

# Constants
MAJOR, MINOR, HOTFIX, *REMAINDER = VERSION.split('.')
CURRENT_FCF_CHECKPOINT_VERSION = '{}.{}.{}'.format(MAJOR, MINOR, HOTFIX)


class FCFCheckpoint():
    """Contains the current autotrageur state.

    Encapsulates values pertaining to the autotrageur run.  Useful for rollback
    situations.
    """

    def __init__(self, config=None, strategy_state=None, stat_tracker=None):
        """Constructor.

        Initializes all state-related objects and variables.  Persists the
        bot's configuration right upon initialization while the others are
        set when required.

        NOTE: We require default arguments to ensure that FCFCheckpoint objects
        will always have all attributes after unpickling.  Whenever we add
        a new parameter, we must ensure that it has a default argument to allow
        proper construction of the object.  `unpickle_checkpoint` will call
        the constructor directly.

        Args:
            config (Configuration): The current Configuration of the bot.
            strategy_state (FCFStrategyState): The current Strategy State of
                the bot.
            stat_tracker (StatTracker): The StatTracker state of the bot.
        """
        self._config = config
        self._strategy_state = strategy_state
        self._stat_tracker = stat_tracker

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
    def stat_tracker(self):
        """Property getter for the checkpoint's stat tracker.

        Returns:
            StatTracker: The checkpoint's saved stat tracker.
        """
        return self._stat_tracker

    @stat_tracker.setter
    def stat_tracker(self, stat_tracker):
        """Property setter for the checkpoint's stat tracker.

        Args:
            stat_tracker (StatTracker): A stat tracker to save into the
                checkpoint.

        Raises:
            TypeError: Raised if not a class or subclass of FCFStatTracker.
        """
        if not isinstance(stat_tracker, FCFStatTracker):
            raise TypeError("a stat tracker must be a class or subclass of "
                "FCFStatTracker.")
        self._stat_tracker = stat_tracker

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
            self.config, self.strategy_state, self.stat_tracker)

    def restore_strategy(self, strategy):
        """Restores a Strategy to its former state.

        Args:
            strategy (FCFStrategy): The current FCFStrategy object, before
                restoration.
        """
        strategy.state = self.strategy_state
        strategy.target_tracker = strategy.state.target_tracker
        strategy.trade_chunker = strategy.state.trade_chunker
