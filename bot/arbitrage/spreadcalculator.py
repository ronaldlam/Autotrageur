import logging


def calc_spread(price1, price2):
    """Calculates the spread between two prices.

    Args:
        price1 (float): The first price.
        price2 (float): The second price.

    Returns:
        float: The calculated spread as a percentage.
    """
    # TODO: Should we format here?
    # TODO: Need to make more robust.
    if price1 is None or price2 is None:
        logging.warning(
            "None input: (price1, price2) = (%s, %s)" % (price1, price2))
        return None
    elif price1 <= 0 or price2 <= 0:
        logging.warning(
            "Negative input: (price1, price2) = (%s, %s)" % (price1, price2))
        return None
    else:
        return (price1/price2 - 1) * 100
