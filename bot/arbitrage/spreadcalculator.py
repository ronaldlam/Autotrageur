import logging
from libs.utilities import num_to_decimal


ZERO = num_to_decimal('0')
NEGATIVE_ONE = num_to_decimal(-1)
HUNDRED = num_to_decimal(100)


def __is_invalid_price(exc2_num_price, exc1_denom_price):
    """Checks price inputs to see if either are None, zero, or negative.

    Args:
        exc2_num_price (Decimal): The price from exchange 2, to be used as
            the numerator for forward spread opportunities.
        exc1_denom_price (Decimal): The price from exchange 1, to be used as
            the denominator for forward spread opportunities.

    Returns:
        bool: Returns True if either price given was None, zero, or negative.
            Else, False.
    """
    if exc2_num_price is None or exc1_denom_price is None:
        logging.warning(
            "None input: (exc2_num_price, exc1_denom_price) = (%s, %s)" %
                (exc2_num_price, exc1_denom_price))
        return True
    elif exc2_num_price <= ZERO or exc1_denom_price <= ZERO:
        logging.warning(
            "Negative input: (exc2_num_price, exc1_denom_price) = (%s, %s)" %
                (exc2_num_price, exc1_denom_price))
        return True
    else:
        return False

def calc_fixed_spread(exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee):
    """Calculates the fixed spread between two prices.  Will not change the
    denominator and calculates a more absolute spread between two prices.

    Subtracts the given exchange trading fees from the calculated spread before
    returning.

    Args:
        exc2_num_price (Decimal): The price from exchange 2, to be used as
            the numerator for forward spread opportunities.
        exc1_denom_price (Decimal): The price from exchange 1, to be used as
            the denominator for forward spread opportunities.
        exc2_fee (Decimal): The trading fee from the second exchange.  Expected
            as a percentage in ratio form (e.g. 0.01 for 1%).
        exc1_fee (Decimal): The trading fee from the first exchange.  Expected
            as a percentage in ratio form (e.g. 0.01 for 1%).

    Returns:
        Decimal: The calculated spread as a percentage.  Positive indicates a
            forward spread opportunity.  Negative indicates a reverse spread
            opportunity.  Returns None if either input price is None, zero or
            negative.
    """
    if __is_invalid_price(exc2_num_price, exc1_denom_price):
        return None
    else:
        raw_spread = ((exc2_num_price - exc1_denom_price)
                       / exc1_denom_price
                       * 100)
        weighted_fees = calc_trade_fees(exc2_num_price, exc1_denom_price,
            exc2_fee, exc1_fee)

        # The spread after fees.
        spread_post_fees = raw_spread - weighted_fees
        if raw_spread < 0:
            spread_post_fees = raw_spread + weighted_fees
        else:
            spread_post_fees = raw_spread - weighted_fees

        logging.info("Calculated raw spread of: {}".format(raw_spread))
        logging.info("Spread post-fees: {} with weighted fees of: {}".format(
            spread_post_fees, weighted_fees))

        return spread_post_fees


def calc_variable_spread(exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee):
    """Calculates the variable spread between two prices. Will change the
    denominator to calculate a more relative spread.

    Subtracts the given exchange trading fees from the calculated spread before
    returning.

    NOTE: When the spread is calculated as a negative number, we flip the
    denominator so that exc2_num_price is used instead of exc1_denom_price
    (default denominator).
    This allows the spread percentage to be interpreted as a profit indicator,
    and a percentage change of growth, rather than a percentage change of
    decay.  This also prevents fees from triggering a false negative in terms
    of putting the spread back over target 'spread_low'.

    Example (without fees):
    (Positive Spread) exc1 of $700, exc2 of $770.  Spread will be:
        ((770 - 700) / 700) * 100 = 10%
        It is a forward spread, so +10% is returned.
    (Negative Spread) exc1 of $770, exc1 of $700.  Spread will be:
        ((770 - 700) / 700) * 100 = 10%
        Turned negative to indicate reverse spread, so -10% is returned.

    Args:
        exc2_num_price (Decimal): The price from exchange 2, to be used as
            the default numerator for forward spread opportunities.  Will be
            used as denominator for reverse spread opportunities.
        exc1_denom_price (Decimal): The price from exchange 1, to be used as the
            default denominator for forward spread opportunities.  Will be used
            as numerator for reverse spread opportunities.
        exc2_fee (Decimal): The trading fee from the second exchange.  Expected
            as a percentage in ratio form (e.g. 0.01 for 1%).
        exc1_fee (Decimal): The trading fee from the first exchange.  Expected
            as a percentage in ratio form (e.g. 0.01 for 1%).

    Returns:
        Decimal: The calculated spread as a percentage.  Positive indicates a
            forward spread opportunity.  Negative indicates a reverse spread
            opportunity.  Returns None if either input price is None, zero or
            negative.
    """
    if __is_invalid_price(exc2_num_price, exc1_denom_price):
        return None
    else:
        is_fwd_spread = exc2_num_price >= exc1_denom_price

        denom = exc1_denom_price if is_fwd_spread else exc2_num_price
        num = exc2_num_price if is_fwd_spread else exc1_denom_price

        # The spread without fees.
        raw_spread = ((num - denom) / denom) * HUNDRED
        if is_fwd_spread:
            weighted_fees = calc_trade_fees(num, denom, exc2_fee, exc1_fee)
        else:
            weighted_fees = calc_trade_fees(num, denom, exc1_fee, exc2_fee)

        # The spread after fees.
        spread_post_fees = (raw_spread - weighted_fees) if is_fwd_spread else (
            (raw_spread - weighted_fees) * NEGATIVE_ONE)

        logging.info("Calculated raw spread of: {}".format(raw_spread))
        logging.info("Spread post-fees: {} with weighted fees of: {}".format(
            spread_post_fees, weighted_fees))

        return spread_post_fees


def calc_trade_fees(price1, price2, fee1, fee2):
    """Calculates the total trading fees from two given prices and two given
    fees corresponding to those prices.

    The higher price will be increased by the ratio of (higher_price
                                                        / lower_price).
    This produces the weighted fee from the higher_price.

    For example:
    Assuming price1 is higher than price2, the weighted fee1 is:
        (price1 / price2) * fee1
    So, if price1 = 1.05 and price2 = 1.00, weighted fee1 will be:
        (1.05 / 1.00) * fee1, 105% more than the original fee1.

    Args:
        price1 (Decimal): The price used as a numerator when calculating
            the weighted fees.
        price2 (Decimal): The price used as denominator when calculating
            the weighted fees.
        fee1 (Decimal): The fee associated with price1.
        fee2 (Decimal): The fee associated with price2

    Returns:
        Decimal: The true weighted trading fee to account for when performing
            trades.
    """
    if price1 == ZERO and price2 == ZERO:
        return ZERO
    elif price1 > ZERO and price2 == ZERO:
        return fee1
    elif price2 > ZERO and price1 == ZERO:
        return fee2

    if price1 > price2:
        num_price = price1
        denom_price = price2
        num_fee = fee1
        denom_fee = fee2
    else:
        num_price = price2
        denom_price = price1
        num_fee = fee2
        denom_fee = fee1

    weighted_num_fee = (num_price / denom_price) * num_fee
    return (weighted_num_fee + denom_fee) * HUNDRED
