import logging
from decimal import Decimal

from libs.utilities import num_to_decimal


ZERO = Decimal('0')

class InsufficientFakeFunds(Exception):
    pass


class DryRunExchange():
    """An object to hold the dry run data of one exchange."""

    def __init__(self, name, base, quote, base_balance, quote_balance):
        """Constructor.

        Args:
            name (str): The exchange name.
            base (str): The base asset. eg. ETH.
            quote (str): The quote asset. eg. USD.
            base_balance (int/float): The initial base balance.
            quote_balance (int/float): The initial quote balance.
        """
        self.name = name
        self.base = base
        self.quote = quote
        self.base_balance = num_to_decimal(base_balance)
        self.quote_balance = num_to_decimal(quote_balance)
        self.base_volume = ZERO
        self.quote_volume = ZERO
        self.base_fees = ZERO
        self.quote_fees = ZERO
        self.trade_count = 0

    def buy(self, pre_fee_base, pre_fee_quote, post_fee_base, post_fee_quote):
        """Exchange quote units of quote asset for base units of base asset.

        Args:
            base (Decimal): Amount of base to exchange for.
            quote (Decimal): Amount of quote to exchange.

        Raises:
            InsufficientFakeFunds: If the dry run balance is insufficient.
        """
        if post_fee_quote > self.quote_balance:
            raise InsufficientFakeFunds(
                'Attempted buy of %s %s on %s. %s %s available.',
                post_fee_quote, self.quote, self.name, self.quote_balance,
                self.quote)
        self.base_balance += post_fee_base
        self.quote_balance -= post_fee_quote
        self.base_volume += pre_fee_base
        self.quote_volume += pre_fee_quote
        self.base_fees += post_fee_base - pre_fee_base
        self.quote_fees += post_fee_quote - pre_fee_quote
        self.trade_count += 1

    def sell(self, base_amount, pre_fee_quote, post_fee_quote):
        """Exchange base units of base asset for quote units of quote asset.

        Args:
            base (Decimal): Amount of base to exchange.
            quote (Decimal): Amount of quote to exchange for.

        Raises:
            InsufficientFakeFunds: If the dry run balance is insufficient.
        """
        if base_amount > self.base_balance:
            raise InsufficientFakeFunds(
                'Attempted sell of %s %s on %s. %s %s available.',
                base_amount, self.base, self.name, self.base_balance,
                self.base)
        self.base_balance -= base_amount
        self.quote_balance += post_fee_quote
        self.base_volume += base_amount
        self.quote_volume += pre_fee_quote
        self.quote_fees += pre_fee_quote - post_fee_quote
        self.trade_count += 1


class DryRun():
    """An object to hold the dry run state of the bot."""

    def __init__(self, exchange1, exchange2):
        """Constructor.

        Args:
            exchange1 (DryRunExchange): The object to hold dry run
                execution state for the first exchange.
            exchange2 (DryRunExchange): The object to hold dry run
                execution state for the second exchange.
        """
        self.e1 = exchange1
        self.e2 = exchange2

    def log_balances(self):
        """Log the current balances of the run."""
        logging.info('Balances:')
        logging.info(self.e1.name)
        logging.info('base: %s %s', self.e1.base_balance, self.e1.base)
        logging.info('quote: %s %s', self.e1.quote_balance, self.e1.quote)
        logging.info(self.e2.name)
        logging.info('base: %s %s', self.e2.base_balance, self.e2.base)
        logging.info('quote: %s %s', self.e2.quote_balance, self.e2.quote)

    def log_all(self):
        """Log all state of the run."""
        self.log_balances()
        logging.info(self.e1.name)
        logging.info('%s volume: %s', self.e1.base, self.e1.base_volume)
        logging.info('%s volume: %s', self.e1.quote, self.e1.quote_volume)
        logging.info('trade count: %s', self.e1.trade_count)
        logging.info(self.e2.name)
        logging.info('%s volume: %s', self.e2.base, self.e2.base_volume)
        logging.info('%s volume: %s', self.e2.quote, self.e2.quote_volume)
        logging.info('trade count: %s', self.e2.trade_count)
