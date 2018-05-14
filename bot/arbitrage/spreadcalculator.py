import logging
from libs.utilities import num_to_decimal


ZERO = num_to_decimal('0')


def calc_spread(price1, price2):
    """Calculates the spread between two prices.

    Args:
        price1 (Decimal): The first price.
        price2 (Decimal): The second price.

    Returns:
        Decimal: The calculated spread as a percentage.
    """
    # TODO: Should we format here?
    # TODO: Need to make more robust.
    if price1 is None or price2 is None:
        logging.warning(
            "None input: (price1, price2) = (%s, %s)" % (price1, price2))
        return None
    elif price1 <= ZERO or price2 <= ZERO:
        logging.warning(
            "Negative input: (price1, price2) = (%s, %s)" % (price1, price2))
        return None
    else:
        return (price1/price2 - num_to_decimal(1)) * num_to_decimal(100)
