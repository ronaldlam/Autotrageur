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
        self.target_index = None
        self.last_target_index = None
        self.h_to_e1_max = None
        self.h_to_e2_max = None

    def save(self, autotrageur):
        """Saves the current autotrageur state before another algorithm
        iteration.

        The rationale for saving `h_to_e1_max` and `h_to_e2_max` is that the
        historical maximums provided by the config file may have been surpassed
        during the bot's run.

        Args:
            autotrageur (FCFAutotrageur): The current FCFAutotrageur.
        """
        self.has_started = autotrageur.has_started
        self.momentum = autotrageur.momentum
        self.e1_targets = autotrageur.e1_targets
        self.e2_targets = autotrageur.e2_targets
        self.target_index = autotrageur.target_index
        self.last_target_index = autotrageur.last_target_index
        self.h_to_e1_max = autotrageur.h_to_e1_max
        self.h_to_e2_max = autotrageur.h_to_e2_max

    def restore(self, autotrageur):
        """Restores the saved autotrageur state.

        Sets relevant FCFAutotrageur's 'self' object attributes to the previously
        saved state.

        Args:
            autotrageur (FCFAutotrageur): The current FCFAutotrageur.
        """
        autotrageur.config[ID] = self.config_id
        autotrageur.has_started = self.has_started
        autotrageur.momentum = self.momentum
        autotrageur.e1_targets = self.e1_targets
        autotrageur.e2_targets = self.e2_targets
        autotrageur.target_index = self.target_index
        autotrageur.last_target_index = self.last_target_index
        autotrageur.h_to_e1_max = self.h_to_e1_max
        autotrageur.h_to_e2_max = self.h_to_e2_max
