import logging

from ccxt import NetworkError
from googletrans import Translator

import bot.arbitrage.spreadcalculator as spreadcalculator
from bot.trader.ccxt_trader import OrderbookException
from libs.utilities import num_to_decimal


BIDS = "bids"
ASKS = "asks"


class AbortTradeException(Exception):
    """Exception signifying a trade abort."""
    pass


class SpreadOpportunity():
    def __init__(self, e1_spread, e2_spread, e1_buy, e2_buy, e1_sell, e2_sell):
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


def execute_arbitrage(trade_metadata):
    """Execute the arbitrage trade.

    The CCXTTraders store information about the ticker, target, and
    exchange details. We verify that the numbers are correct once more
    before execution.

    Args:
        trade_metadata (dict): Metadata relevant to executing the current trade
            opportunity

    Returns:
        bool: True if succeeded
    """
    buy_trader = trade_metadata['buy_trader']
    sell_trader = trade_metadata['sell_trader']
    buy_price = trade_metadata['buy_price']
    sell_price = trade_metadata['sell_price']

    try:
        logging.info("Buy price: %s, Sell price %s" % (buy_price, sell_price))
        buy_result = buy_trader.execute_market_buy(buy_price)
        logging.info("Buy result: %s" % buy_result)
        executed_buy_amount = buy_result["info"]["executed_amount"]

        # TODO: What happens if buy succeeds and sell fails?
        sell_result = sell_trader.execute_market_sell(
            sell_price,
            num_to_decimal(executed_buy_amount))
        logging.info("Sell result: %s" % sell_result)
        return True
    except NetworkError as network_err:
        logging.error(network_err, exc_info=True)
        return False
    except Exception as exception:
        t = Translator()
        decoded = exception.args[0].encode('utf-8').decode('unicode_escape')
        translation = t.translate(decoded)
        logging.error(translation.text)
        return False
