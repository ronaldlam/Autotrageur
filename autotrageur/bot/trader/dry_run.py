from fp_libs.constants.decimal_constants import ZERO
from fp_libs.utilities import num_to_decimal


class InsufficientFakeFunds(Exception):
    """Exception for insufficient funds on dry run exchanges."""
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
        self.base_fees = ZERO
        self.quote_fees = ZERO
        self.trade_count = 0

    def deposit(self, asset, amount, fee=ZERO):
        """Deposit given amount of asset to exchange.

        Args:
            asset (str): The asset symbol.
            amount (Decimal): The deposit amount.
            fee (Decimal): The deposit fee.

        Raises:
            ValueError: If the asset symbol does not match those
                available.
        """
        if asset == self.base:
            self.base_balance += amount - fee
            self.base_fees += fee
        elif asset == self.quote:
            self.quote_balance += amount - fee
            self.quote_fees += fee
        else:
            raise ValueError('Asset type does not match dryrun base or quote.')

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
        self.base_fees += pre_fee_base - post_fee_base
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
        self.quote_fees += pre_fee_quote - post_fee_quote
        self.trade_count += 1

    def withdraw(self, asset, amount, fee=ZERO):
        """Withdraw given amount of asset from exchange.

        Args:
            asset (str): The asset symbol.
            amount (Decimal): The withdrawal amount.
            fee (Decimal): The withdrawal fee.

        Raises:
            ValueError: If the asset symbol does not match those
                available.
        """
        if asset == self.base:
            self.base_balance -= amount
            self.base_fees += fee
        elif asset == self.quote:
            self.quote_balance -= amount
            self.quote_fees += fee
        else:
            raise ValueError('Asset type does not match dryrun base or quote.')
