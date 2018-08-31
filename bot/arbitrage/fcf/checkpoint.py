from bot.common.config_constants import ID


class FCFCheckpoint():
    """Contains the current algorithm state.

    Encapsulates values pertaining to the algorithm.  Useful for rollback
    situations.
    """

    def __init__(self, config_id):
        """Constructor.

        Initializes variables and sets the configuration ID used for the bot
        run.  Note that if the bot is started as a resumed run, the
        configuration ID is eventually overwritten with a previously created
        ID.

        Args:
            config_id (str): The unique configuration ID created for this bot
                run.
        """
        self.config_id = config_id
        self.has_started = False
        self.momentum = None
        self.e1_targets = None
        self.e2_targets = None
        self.h_to_e1_max = None
        self.h_to_e2_max = None
        self.target_tracker = None
        self.trade_chunker = None

    def save(self, strategy):
        """Saves the current strategy state before another algorithm
        iteration.

        The rationale for saving `h_to_e1_max` and `h_to_e2_max` is that the
        historical maximums provided by the config file may have been surpassed
        during the bot's run.

        Args:
            strategy (FCFStrategy): The current FCFStrategy.
        """
        self.has_started = strategy.has_started
        self.momentum = strategy.momentum
        self.e1_targets = strategy.e1_targets
        self.e2_targets = strategy.e2_targets
        self.h_to_e1_max = strategy.h_to_e1_max
        self.h_to_e2_max = strategy.h_to_e2_max
        self.target_tracker = strategy.target_tracker
        self.trade_chunker = strategy.trade_chunker

    def restore(self, strategy):
        """Restores the saved strategy state.

        Sets relevant FCFStrategy's 'self' object attributes to the previously
        saved state.

        Args:
            strategy (FCFStrategy): The current FCFStrategy.
        """
        strategy.config[ID] = self.config_id
        strategy.has_started = self.has_started
        strategy.momentum = self.momentum
        strategy.e1_targets = self.e1_targets
        strategy.e2_targets = self.e2_targets
        strategy.h_to_e1_max = self.h_to_e1_max
        strategy.h_to_e2_max = self.h_to_e2_max
        strategy.target_tracker = self.target_tracker
        strategy.trade_chunker = self.trade_chunker
