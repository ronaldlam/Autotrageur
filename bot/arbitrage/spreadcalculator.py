import logging


def calc_spread(exc1_price, exc2_price, exc1_fee, exc2_fee):
    """Calculates the spread between two prices.

    Subtracts the given exchange trading fees from the calculated spread before
    returning.

    Args:
        exc1_price (float): The first price from the first exchange.
        exc2_price (float): The second price from the second exchange.
        exc1_fee (float): The first fee from the first exchange.  Expected as a
            percentage in ratio form (e.g. 0.01 for 1%).
        exc2_fee (float): The second fee from the second exchange.  Expected as
            a percentage in ratio form (e.g. 0.01 for 1%).

    Returns:
        float: The calculated spread as a percentage.
    """
    # TODO: Should we format here?
    # TODO: Need to make more robust.
    if exc1_price is None or exc2_price is None:
        logging.warning(
            "None input: (exc1_price, exc2_price) = (%s, %s)" %
                (exc1_price, exc2_price))
        return None
    elif exc1_price <= 0 or exc2_price <= 0:
        logging.warning(
            "Negative input: (exc1_price, exc2_price) = (%s, %s)" %
                (exc1_price, exc2_price))
        return None
    else:
        raw_spread = (exc1_price/exc2_price - 1) * 100
        spread_post_fees = raw_spread - (exc1_fee * 100 + exc2_fee * 100)

        logging.info("Calculated raw spread of: {}".format(raw_spread))
        logging.info("Spread post-fees: {}".format(spread_post_fees))

        return spread_post_fees
