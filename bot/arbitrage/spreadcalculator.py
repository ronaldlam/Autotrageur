def calc_spread(price1, price2):
    """Calculates the spread between two prices.

    Args:
        price1 (float): The first price.
        price2 (float): The second price.

    Returns:
        float: The calculated spread.  Anything greater than 1 will be a
               positive spread.
    """
    # TODO: Should we format here?
    # TODO: Need to make more robust.
    return price1/price2