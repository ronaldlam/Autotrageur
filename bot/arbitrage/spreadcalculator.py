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
    return (price1/price2 - 1) * 100