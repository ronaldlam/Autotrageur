from forex_python.converter import CurrencyRates

class BaseAPIClient:
    """Base class for an API client."""

    def __init__(self, base, quote, exchange):
        """Constructor.

        Args:
            base (str): The base (first) token/currency of the exchange pair.
            quote (str): The quote (second) token/currency of the exchange pair.
            exchange (str): Desired exchange to query against.
        """
        self.base = base
        self.quote = quote
        self.exchange = exchange

    def convert_to_usd(self, amount):
        """Converts an amount of quoted currency to usd.

        Args:
            amount (float): The amount of quoted currency to convert.
        """
        # TODO: Probably better practice to have a converter module.
        # NOTE: With forex_python, the forex rates are updated only daily.
        converter = CurrencyRates()
        return converter.convert(self.quote, 'USD', amount)
