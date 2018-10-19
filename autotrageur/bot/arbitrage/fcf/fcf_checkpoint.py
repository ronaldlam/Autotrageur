from setuptools_scm import get_version

from autotrageur.bot.arbitrage.autotrageur import Configuration
from autotrageur.bot.arbitrage.fcf.strategy import FCFStrategyState
from autotrageur.bot.trader.dry_run import DryRunManager

# Constants
VERSION = get_version()
MAJOR, MINOR, HOTFIX, *REMAINDER = VERSION
CURRENT_FCF_CHECKPOINT_VERSION = '{}.{}'.format(MAJOR, MINOR)


class FCFCheckpoint():
    """Contains the current autotrageur state.

    Encapsulates values pertaining to the autotrageur run.  Useful for rollback
    situations.
    """

    def __init__(self, config=None, strategy_state=None, dry_run_manager=None):
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
            config (Configuration): The current Configuration of the autotrageur.bot.
        """
        self._config = config
        self._strategy_state = strategy_state
        self._dry_run_manager = dry_run_manager

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

    def restore_strategy(self, strategy):
        """Restores a Strategy to its former state.

        Args:
            strategy (FCFStrategy): The current FCFStrategy object, before
                restoration.
        """
        strategy.state = self.strategy_state
        strategy.target_tracker = strategy.state.target_tracker
        strategy.trade_chunker = strategy.state.trade_chunker
