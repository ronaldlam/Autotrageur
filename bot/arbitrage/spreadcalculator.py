import logging

from bot.common.decimal_constants import ZERO, ONE, NEGATIVE_ONE, HUNDRED
from libs.utilities import num_to_decimal


def _is_invalid_price(exc2_num_price, exc1_denom_price):
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
            "Zero or negative input: "
            "(exc2_num_price, exc1_denom_price) = (%s, %s)" %
                (exc2_num_price, exc1_denom_price))
        return True
    else:
        return False

def calc_fixed_spread(buy_price, sell_price, buy_fee, sell_fee, buy_incl_fee):
    """Calculates the fixed spread between two prices.  Will not change the
    denominator and calculates a more absolute spread between two prices.

    Applies the given exchange trading fees from the calculated spread before
    returning.  The equation used is dependent upon how fees are factored into
    an exchange's 'buy order'.  This variable is represented by `buy_incl_fee`.
    An exchange can either:

    1) Charge fees inclusive with the buy order.  E.g. $1000 with a 1% fee will
       end up as a $990 buy order and $10 in fees.
    2) Charge fees on top of the buy order.  E.g. $1000 with a 1% fee will cost
       $1010 overall.

    The equation used in Scenario 1 is:
    y = (x/bp * (1 - bf)) * sp * (1 - sf)

    And Scenario 2:
    y = (x/bp / (1 + bf)) * sp * (1 - sf)

    where:
        - y is the amount of quote acquired
        - x is the amount of quote to purchase with
        - bp is the buy exchange's price (buy_price)
        - bf is the buy exchange's fee (buy_fee)
        - sp is the sell exchange's price (sell_price)
        - sf is the sell exchange's fee (sell_fee)

    Args:
        buy_price (Decimal): The price from the buy exchange, to be used as
            the numerator for spread opportunities.
        sell_price (Decimal): The price from the sell exchange, to be used as
            the denominator for spread opportunities.
        buy_fee (Decimal): The trading fee from the buy exchange.  Expected
            as a percentage in ratio form (e.g. 0.01 for 1%).
        sell_fee (Decimal): The trading fee from the sell exchange.  Expected
            as a percentage in ratio form (e.g. 0.01 for 1%).
        buy_incl_fee (bool): True if an exchange's `buy_price` will have fees
            factored into the price (Scenario 1, as described above). Else,
            False.

    Returns:
        Decimal: The calculated spread as a percentage. Returns None if either
            input price is None, zero or negative.
    """
    if _is_invalid_price(buy_price, sell_price):
        return None
    else:
        if buy_incl_fee:
            spread = ((ONE / buy_price)
                    * (ONE - buy_fee)
                    * sell_price
                    * (ONE - sell_fee) - ONE) * HUNDRED

        else:
            spread = ((ONE / buy_price)
                    / (ONE + buy_fee)
                    * sell_price
                    * (ONE - sell_fee) - ONE) * HUNDRED

        logging.debug("Calculated spread of: {}\nWith buy price {} buy fee {}\n"
            "With sell price {} sell fee {}".format(spread, buy_price,
                                                    buy_fee, sell_price,
                                                    sell_fee))
        return spread
