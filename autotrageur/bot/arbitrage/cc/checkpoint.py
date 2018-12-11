from autotrageur.bot.arbitrage.cc.configuration import CCConfiguration
from autotrageur.bot.arbitrage.cc.stat_tracker import CCStatTracker
from autotrageur.bot.arbitrage.cc.strategy import CCStrategyState
from autotrageur.version import VERSION

# Constants
MAJOR, MINOR, HOTFIX, *REMAINDER = VERSION.split('.')
CURRENT_CC_CHECKPOINT_VERSION = '{}.{}.{}'.format(MAJOR, MINOR, HOTFIX)


class CCCheckpoint():
    """Contains the current autotrageur state.

    Encapsulates values pertaining to the autotrageur run.  Useful for
    rollback situations.
    """
    def __init__(self, config=None, strategy_state=None, stat_tracker=None):
        """Constructor.

        Initializes all state-related objects and variables.  Persists the
        bot's configuration right upon initialization while the others are
        set when required.

        NOTE: We require default arguments to ensure that CCCheckpoint objects
        will always have all attributes after unpickling.  Whenever we add
        a new parameter, we must ensure that it has a default argument to allow
        proper construction of the object. The `unpickle_checkpoint` function
        will call the constructor directly.

        Args:
            config (CCConfiguration): The current CCConfiguration of the bot.
            strategy_state (CCStrategyState): The current Strategy State of
                the bot.
            stat_tracker (CCStatTracker): The StatTracker state of the bot.
        """
        self._config = config
        self._strategy_state = strategy_state
        self._stat_tracker = stat_tracker

    @property
    def config(self):
        """Property getter for the checkpoint's config.

        Returns:
            CCConfiguration: The checkpoint's saved config.
        """
        return self._config

    @config.setter
    def config(self, config):
        """Property setter for the checkpoint's config.

        Args:
            config (CCConfiguration): A configuration to save into the checkpoint.

        Raises:
            TypeError: Raised if not type CCConfiguration.
            AttributeError: Raised if an CCConfiguration has already been
                saved in the checkpoint - ensuring that the config is not
                accidentally overwritten.
        """
        if not isinstance(config, CCConfiguration):
            raise TypeError("config must be of type CCConfiguration.")
        if hasattr(self, '_config'):
            raise AttributeError("a CCConfiguration cannot be changed during a "
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
            TypeError: Raised if not a class or subclass of CCStatTracker.
        """
        if not isinstance(stat_tracker, CCStatTracker):
            raise TypeError("A stat tracker must be a class or subclass of "
                            "CCStatTracker.")
        self._stat_tracker = stat_tracker

    @property
    def strategy_state(self):
        """Property getter for the checkpoint's strategy state.

        Returns:
            CCStrategyState: The checkpoint's saved strategy state.
        """
        return self._strategy_state

    @strategy_state.setter
    def strategy_state(self, strategy_state):
        """Property setter for the checkpoint's strategy state.

        Args:
            strategy_state (CCStrategyState): A strategy state to save into the
                checkpoint.

        Raises:
            TypeError: Raised if not type CCStrategyState.
        """
        if not isinstance(strategy_state, CCStrategyState):
            raise TypeError("strategy state must be of type CCStrategyState.")
        self._strategy_state = strategy_state

    def __repr__(self):
        """Printable representation of the CCCheckpoint, for debugging."""
        return "CCCheckpoint state objects:\n{0!r}\n{1!r}\n{2!r}".format(
            self.config, self.strategy_state, self.stat_tracker)

    def restore_strategy(self, strategy):
        """Restores a Strategy to its former state.

        Args:
            strategy (CCStrategy): The current CCStrategy object, before
                restoration.
        """
        strategy.state = self.strategy_state
        strategy.trade_chunker = strategy.state.trade_chunker
