from forex_python.converter import CurrencyRates

CURRENCY_CONVERTER = CurrencyRates()


class UnacceptableAmountException(Exception):
    """Thrown when trying to convert an amount less than 0

    NOTE: This is because the forex_python library will throw a misleading
    exception if trying to convert an amount of less than 0.
    """
    pass


def convert_currencies(from_curr, to_curr, amount):
    """Converts a specified amount of currency into another currency.

    Args:
        from_curr (str): Ticker of currency to convert from.
        to_curr (str): Ticker of currency to convert to.
        amount (Decimal): The amount of currency to convert.

    Raises:
        UnacceptableAmountException: Thrown when the amount of currency is
                                     less than 0.

    Returns:
        Decimal: The converted amount of currency.
    """
    if amount < 0:
        raise UnacceptableAmountException("The amount to be converted must be greater than 0")
    return CURRENCY_CONVERTER.convert(from_curr, to_curr, amount)
