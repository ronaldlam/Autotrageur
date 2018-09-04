class FCFCheckpoint():
    """Contains the current autotrageur state.

    Encapsulates values pertaining to the autotrageur run.  Useful for rollback
    situations.
    """

    # TODO: @property for all saved components
    def __init__(self, config):
        """Constructor.

        Initializes all state-related objects and variables.  Persists the
        bot's configuration right upon initialization while the others are
        set when required.

        Args:
            config (Configuration): The current Configuration of the bot.
        """
        self.config = config
        # TODO: Should dry run be initialized outside of setup_traders so that
        # it can be passed in?
        self.dry_run_manager = None
        self.strategy_state = None

    def __repr__(self):
        """Printable representation of the FCFCheckpoint, for debugging."""
        return "FCFCheckpoint state objects:\n{}\n{}\n{}".format(
            self.config, self.strategy_state.__dict__, self.dry_run_manager.__dict__)

    def save_strategy_state(self, strategy_state):
        """Saves the current strategy state before another algorithm
        iteration.

        The rationale for saving `h_to_e1_max` and `h_to_e2_max` is that the
        historical maximums provided by the config file may have been surpassed
        during the bot's run.

        Args:
            strategy_state (FCFStrategyState): The current state of the
                FCFStrategy.
        """
        self.strategy_state = strategy_state

    def restore_strategy_state(self, strategy_state):
        """Restores the strategy state to the previously saved state.

        Args:
            strategy_state (FCFStrategyState): The current state of the
                FCFStrategy.
        """
        strategy_state = self.strategy_state

    def restore_bot_state_from_checkpoint(self, config, strategy_state,
                                          dry_run_manager):
        """Restores any state relevant to the bot.

        Component states restored:
        - Algorithm
        - Configuration
        - DryRun (if in dry run mode)

        Args:
            config (Configuration): The current configuration of the bot.
            strategy_state (FCFStrategyState): The current state of the
                FCFStrategy.
            dry_run_manager (DryRunManager): If on dry run mode, the current
                DryRunManager of the bot.  If not on dry run mode, this
                parameter will be `None`.
        """
        strategy_state = self.strategy_state
        config = self.config

        if dry_run_manager:
            dry_run_manager = self.dry_run_manager
