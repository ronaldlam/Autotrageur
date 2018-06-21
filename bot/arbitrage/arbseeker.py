import logging

from ccxt import NetworkError

import bot.arbitrage.spreadcalculator as spreadcalculator
from bot.trader.ccxt_trader import OrderbookException
from libs.utilities import num_to_decimal


BIDS = "bids"
ASKS = "asks"


class SpreadOpportunity():
    """Structure containing spread and price info for an arbitrage
    opportunity.
    """

    def __init__(self, e1_spread, e2_spread, e1_buy, e2_buy, e1_sell, e2_sell):
        """Constructor."""
        self.e1_spread = e1_spread
        self.e2_spread = e2_spread
        self.e1_buy = e1_buy
        self.e2_buy = e2_buy
        self.e1_sell = e1_sell
        self.e2_sell = e2_sell

def get_spreads_by_ob(trader1, trader2):
    """Obtains spreads across two exchanges based on orderbook.

    Uses two real-time api clients to obtain orderbook information, calculate
    the market buy/sell orders to fulfill the quote target amount set in the
    clients.

    Args:
        trader1 (CCXTTrader): The trading client for exchange 1.
        trader2 (CCXTTrader): The trading client for exchange 2.

    Returns:
        SpreadOpportunity: Returns an object containing the spreads and prices
            pertaining to the current spread opportunity.
    """
    ex1_orderbook = trader1.get_full_orderbook()
    ex2_orderbook = trader2.get_full_orderbook()

    # Exceptions are caught here because we want all the data regardless.
    try:
        e1_buy = trader1.get_adjusted_market_price_from_orderbook(
            ex1_orderbook[ASKS])
    except OrderbookException:
        e1_buy = None
    try:
        e1_sell = trader1.get_adjusted_market_price_from_orderbook(
            ex1_orderbook[BIDS])
    except OrderbookException:
        e1_sell = None
    try:
        e2_buy = trader2.get_adjusted_market_price_from_orderbook(
            ex2_orderbook[ASKS])
    except OrderbookException:
        e2_buy = None
    try:
        e2_sell = trader2.get_adjusted_market_price_from_orderbook(
            ex2_orderbook[BIDS])
    except OrderbookException:
        e2_sell = None

    logging.info("%s buy of %s, %s price: %s" %
                 (trader1.exchange_name, trader1.quote_target_amount,
                  trader1.base, e1_buy))
    logging.info("%s buy of %s, %s price: %s" %
                 (trader2.exchange_name, trader2.quote_target_amount,
                  trader2.base, e2_buy))
    logging.info("%s sell of %s, %s price: %s" %
                 (trader1.exchange_name, trader1.quote_target_amount,
                  trader1.base, e1_sell))
    logging.info("%s sell of %s, %s price: %s" %
                 (trader2.exchange_name, trader2.quote_target_amount,
                  trader2.base, e2_sell))

    # Calculate the spreads between exchange 1 and 2, including taker fees.
    e1_spread = spreadcalculator.calc_fixed_spread(
        e2_buy, e1_sell, trader2.get_taker_fee(),
        trader1.get_taker_fee())
    e2_spread = spreadcalculator.calc_fixed_spread(
        e1_buy, e2_sell, trader1.get_taker_fee(),
        trader2.get_taker_fee())

    logging.info("Ex2 (%s) buy Ex1 (%s) sell e1_spread: (%s)" %
                 (trader2.exchange_name,
                  trader1.exchange_name,
                  e1_spread))
    logging.info("Ex1 (%s) buy Ex2 (%s) sell e2_spread: (%s)" %
                 (trader1.exchange_name,
                  trader2.exchange_name,
                  e2_spread))

    return SpreadOpportunity(e1_spread, e2_spread, e1_buy, e2_buy, e1_sell,
        e2_sell)


def execute_buy(trader, price):
    """Execute buy trade for arbitrage opportunity.

    Args:
        trader (CCXTTrader): The trader for the buy exchange.
        price (Decimal): The buy price for emulated market orders.

    Returns:
        Decimal: The base asset amount purchased.
    """
    logging.info("Buy price: %s" % (price))
    buy_result = trader.execute_market_buy(price)
    logging.info("Buy result: %s" % buy_result)
    # TODO: 'executed_amount' is not unified per all exchanges.  See #90.
    return num_to_decimal(buy_result["info"]["executed_amount"])


def execute_sell(trader, price, executed_amount):
    """Execute sell trade for arbitrage opportunity.

    Args:
        trader (CCXTTrader): The trader for the sell exchange.
        price (Decimal): The sell price for emulated market orders.
        executed_amount (Decimal): The base asset amount which was purchased.
    """
    sell_result = trader.execute_market_sell(
        price,
        executed_amount)
    logging.info("Sell result: %s" % sell_result)
    # TODO: Verify contents of sell_result.
