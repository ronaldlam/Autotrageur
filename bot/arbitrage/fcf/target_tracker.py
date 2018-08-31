import logging


class FCFTargetTracker():

    def __init__(self):
        """Constructor."""
        self.target_index = 0
        self.last_target_index = 0

    def advance_target_index(self, spread, targets):
        """Increment the target index to minimum target greater than
        spread.

        Args:
            spread (Decimal): The calculated spread.
            targets (list): The list of targets.
        """
        while (self.target_index + 1 < len(targets) and
                spread >= targets[self.target_index + 1][0]):
            logging.debug(
                '#### target_index before: {}'.format(self.target_index))
            self.target_index += 1
            logging.debug(
                '#### target_index after: {}'.format(self.target_index))

    def change_momentum(self):
        """Signal a momentum change, resets target_index."""
        self.target_index = 0

    def get_trade_volume(self, targets, is_momentum_change):
        """Retrieve the target trade volume for the current target.

        Args:
            targets (list): The list of targets.
            is_momentum_change (bool): The momentum change indicator

        Returns:
            Decimal: The target trade volume in USD.
        """
        if self.target_index >= 1 and not is_momentum_change:
            return targets[self.target_index][1] - \
                targets[self.last_target_index][1]
        else:
            return targets[self.target_index][1]

    def has_hit_targets(self, spread, targets, is_momentum_change):
        """Indicates whether a target was hit.

        Args:
            spread (Decimal): The spread to evaluate.
            targets (list): The list of targets.
            is_momentum_change (bool): The momentum change indicator.

        Returns:
            bool: Whether a target was hit.
        """
        if is_momentum_change:
            return spread >= targets[0][0]
        else:
            within_len = self.target_index < len(targets)
            return within_len and spread >= targets[self.target_index][0]

    def increment(self):
        """Increment the internal target index and save the current index."""
        self.last_target_index = self.target_index
        self.target_index += 1
        logging.debug('#### target_index advanced by one, is now: {}'.format(
            self.target_index))
