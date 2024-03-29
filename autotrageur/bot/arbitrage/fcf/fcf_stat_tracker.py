import logging


class FCFStatTracker():
    """An object used to track statistics and basic metrics for an FCF bot.

    The statistics are persisted into the DB for external reporting and
    analysis."""

    def __init__(self, new_id, e1_trader, e2_trader):
        """Constructor.

        Args:
            new_id (str): The unique ID for this Stat Tracker.
            e1_trader (CCXTTrader): The Trader object responsible for E1.  Used
                to extract information specific to E1.
            e2_trader (CCXTTrader): The Trader object responsible for E2.  Used
                to extract information specific to E2.
        """
        self.id = new_id
        self.e1 = e1_trader
        self.e2 = e2_trader
        self.dry_run_e1 = e1_trader.dry_run_exchange
        self.dry_run_e2 = e2_trader.dry_run_exchange
        self.trade_count = 0

    def attach_traders(self, e1_trader, e2_trader):
        """Attaches initialized traders to the StatTracker.

        Args:
            e1_trader (CCXTTrader): The Trader object responsible for E1.  Used
                to extract information specific to E1.
            e2_trader (CCXTTrader): The Trader object responsible for E2.  Used
                to extract information specific to E2.
        """
        self.e1 = e1_trader
        self.e2 = e2_trader

    def detach_traders(self):
        """Removes the Trader objects to prepare the StatTracker for
        pickling.

        NOTE: The Trader objects are not able to be pickled, and we do not have
        any intention to persist them.
        """
        del self.e1
        del self.e2

    def log_balances(self):
        """Log the current balances of each exchange."""
        logging.info('Balances:')
        logging.info(self.e1.exchange_name)
        logging.info('base: %s %s', self.e1.base_bal, self.e1.base)
        logging.info('quote: %s %s', self.e1.quote_bal, self.e1.quote)
        logging.info(self.e2.exchange_name)
        logging.info('base: %s %s', self.e2.base_bal, self.e2.base)
        logging.info('quote: %s %s', self.e2.quote_bal, self.e2.quote)

    def log_all(self):
        """Log all the measured statistics of the run."""
        self.log_balances()
        logging.info('Total trade count: %s', self.trade_count)
