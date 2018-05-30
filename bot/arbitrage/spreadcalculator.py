import logging
from libs.utilities import num_to_decimal


ZERO = num_to_decimal('0')
ONE = num_to_decimal('1')
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

def calc_fixed_spread(buy_price, sell_price, buy_fee, sell_fee):
    """Calculates the fixed spread between two prices.  Will not change the
    denominator and calculates a more absolute spread between two prices.

    Applies the given exchange trading fees from the calculated spread before
    returning.  The equation used to calculate the spread with fees is:

    (x/p2 * (1 - f2)) * p1 * (1 - f1), where:
        - x is the amount of quote to purchase with
        - p2 is the buy exchange's price (buy_price)
        - f2 is the buy exchange's fee (buy_fee)
        - p1 is the sell exchange's price (sell_price)
        - f1 is the sell exchange's fee (sell_fee)

    Args:
        buy_price (Decimal): The price from exchange 2, to be used as
            the numerator for spread opportunities.
        sell_price (Decimal): The price from exchange 1, to be used as
            the denominator for spread opportunities.
        buy_fee (Decimal): The trading fee from the second exchange.  Expected
            as a percentage in ratio form (e.g. 0.01 for 1%).
        sell_fee (Decimal): The trading fee from the first exchange.  Expected
            as a percentage in ratio form (e.g. 0.01 for 1%).

    Returns:
        Decimal: The calculated spread as a percentage. Returns None if either
            input price is None, zero or negative.
    """
    if __is_invalid_price(buy_price, sell_price):
        return None
    else:
        spread = ((ONE / buy_price)
                 * (ONE - buy_fee)
                 * sell_price
                 * (ONE - sell_fee) - ONE) * HUNDRED

        logging.info("Calculated spread of: {}\nWith buy price {} buy fee {}\n"
            "With sell price {} sell fee {}".format(spread, buy_price,
                                                    buy_fee, sell_price,
                                                    sell_fee))

        return spread
