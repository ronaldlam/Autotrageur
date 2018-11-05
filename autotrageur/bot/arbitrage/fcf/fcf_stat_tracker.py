import logging
from abc import ABC, abstractmethod

from fp_libs.constants.decimal_constants import ONE
from fp_libs.utilities import num_to_decimal


class AbstractStatTracker(ABC):
    """Abstract class for StatTrackers.  StatTrackers are objects used to track
    statistics and basic metrics for a bot."""

    def __init__(self, new_id, e1_trader, e2_trader):
        self.id = new_id
        self.e1 = e1_trader
        self.e2 = e2_trader
        self.trade_count = 0

    @abstractmethod
    def get_total_poll_success_rate(self):
        pass

    def log_balances(self):
        """Log the current balances of the run."""
        logging.info('Balances:')
        logging.info(self.e1.exchange_name)
        logging.info('base: %s %s', self.e1.base_bal, self.e1.base)
        logging.info('quote: %s %s', self.e1.quote_bal, self.e1.quote)
        logging.info(self.e2.exchange_name)
        logging.info('base: %s %s', self.e2.base_bal, self.e2.base)
        logging.info('quote: %s %s', self.e2.quote_bal, self.e2.quote)

    def log_all(self):
        """Log all state of the run."""
        self.log_balances()
        logging.info('Total trade count: %s', self.trade_count)


class FCFLiveStatTracker(AbstractStatTracker):
    """An object used to track statistics and basic metrics for a live bot."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.total_polls_attempted = 0
        self.total_polls_failed = 0
        # TODO: Would be nice to have specific exchange poll failing stats.

    def get_total_poll_success_rate(self):
        return (ONE - (
            num_to_decimal(self.total_polls_failed)
            / num_to_decimal(self.total_polls_attempted)))

    def log_balances(self):
        super().log_balances()

    def log_all(self):
        super().log_all()


class FCFDryRunStatTracker(AbstractStatTracker):
    """An object used to track statistics and basic metrics for a dry run
    bot."""

    def __init__(self, **kwargs):
        # TODO: There is also the option of passing in the DryRunExchange instead
        # of CCXTTrader as there could be a chance of having the bot's
        # DryRunExchange balances be out of sync with CCXTTrader balances when
        # the bot is killed.  However, the StatTracker hierarchy will be very
        # fragile since DryRunExchange and CCXTTrader are not related classes.

        # To consider accessing DryRunExchange directly, I believe we should
        # create some objects (i.e. Exchange, Wallet) for CCXTTrader to
        # encapsulate different information, and then have an `exchange` attr
        # be accessible here.

        # If we do not want to pass in DryRunExchange directly, it is possible to
        # just disrupt the hierarchy and have one impl.
        super().__init__(**kwargs)
        self.total_polls_attempted = 0
        self.total_polls_failed = 0

    def get_total_poll_success_rate(self):
        return num_to_decimal('1.00')

    def log_balances(self):
        super().log_balances()

    def log_all(self):
        super().log_all()
