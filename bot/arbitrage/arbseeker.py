from collections import namedtuple
import logging

from ccxt import NetworkError

import bot.arbitrage.spreadcalculator as spreadcalculator
from bot.trader.ccxt_trader import OrderbookException
from libs.utilities import num_to_decimal


BIDS = "bids"
ASKS = "asks"
BUY = "buy"
SELL = "sell"
E1_BUY = 0
E1_SELL = 1
E2_BUY = 2
E2_SELL = 3


# Structure for data required to retrieve price data for one side on one
# exchange.
PriceEntry = namedtuple(
    'PriceEntry', ['price_type', 'side', 'trader', 'bids_or_asks'])
# Structure containing spread and price info for an arbitrage opportunity.
SpreadOpportunity = namedtuple(
    'SpreadOpportunity',
    ['e1_spread', 'e2_spread', 'e1_buy', 'e2_buy', 'e1_sell', 'e2_sell'])


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

    prices = [None] * 4
    price_data = [
        PriceEntry(E1_BUY, BUY, trader1, ex1_orderbook[ASKS]),
        PriceEntry(E1_SELL, SELL, trader1, ex1_orderbook[BIDS]),
        PriceEntry(E2_BUY, BUY, trader2, ex2_orderbook[ASKS]),
        PriceEntry(E2_SELL, SELL, trader2, ex2_orderbook[BIDS])
    ]

    # Exceptions are caught here because we want all the data regardless.
    for item in price_data:
        try:
            prices[item.price_type] = item.trader.get_prices_from_orderbook(
                item.bids_or_asks)
        except OrderbookException:
            pass

        logging.info("%s %s of %s %s of %s, price: %s USD",
                        item.trader.exchange_name,
                        item.side,
                        item.trader.quote_target_amount,
                        item.trader.quote,
                        item.trader.base,
                        prices[item.price_type].usd_price)

    # Calculate the spreads between exchange 1 and 2, including taker fees.
    e1_spread = spreadcalculator.calc_fixed_spread(
        prices[E2_BUY].usd_price, prices[E1_SELL].usd_price,
        trader2.get_taker_fee(), trader1.get_taker_fee(),
        trader2.get_buy_target_includes_fee())
    e2_spread = spreadcalculator.calc_fixed_spread(
        prices[E1_BUY].usd_price, prices[E2_SELL].usd_price,
        trader1.get_taker_fee(), trader2.get_taker_fee(),
        trader1.get_buy_target_includes_fee())

    logging.info("Ex2 (%s) buy Ex1 (%s) sell e1_spread: (%s)" %
                 (trader2.exchange_name,
                  trader1.exchange_name,
                  e1_spread))
    logging.info("Ex1 (%s) buy Ex2 (%s) sell e2_spread: (%s)" %
                 (trader1.exchange_name,
                  trader2.exchange_name,
                  e2_spread))

    return SpreadOpportunity(
        e1_spread, e2_spread, prices[E1_BUY].quote_price,
        prices[E2_BUY].quote_price, prices[E1_SELL].quote_price,
        prices[E2_SELL].quote_price)


def execute_buy(trader, price):
    """Execute buy trade for arbitrage opportunity.

    Args:
        trader (CCXTTrader): The trader for the buy exchange.
        price (Decimal): The buy price for emulated market orders.

    Raises:
        NotImplementedError: If not implemented.
        ExchangeLimitException: If asset buy amount is outside
            exchange limits.

    Returns:
        dict: The Autotrageur specific unified buy response.
    """
    logging.debug("Buy price: %s" % (price))
    buy_result = trader.execute_market_buy(price)
    logging.info("Buy result: %s" % buy_result)
    return buy_result


def execute_sell(trader, price, executed_amount):
    """Execute sell trade for arbitrage opportunity.

    Args:
        trader (CCXTTrader): The trader for the sell exchange.
        price (Decimal): The sell price for emulated market orders.
        executed_amount (Decimal): The base asset amount which was purchased.

    Raises:
        NotImplementedError: If not implemented.
        ExchangeLimitException: If asset sell amount is outside
            exchange limits.

    Returns:
        dict: The Autotrageur specific unified sell response.
    """
    logging.debug("Sell price: %s, Base volume: %s" % (price, executed_amount))
    sell_result = trader.execute_market_sell(
        price,
        executed_amount)
    logging.info("Sell result: %s" % sell_result)
    return sell_result
