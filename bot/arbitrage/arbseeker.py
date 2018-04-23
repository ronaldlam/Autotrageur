import logging

from googletrans import Translator

import bot.arbitrage.spreadcalculator as spreadcalculator
import bot.trader.ccxt_trader as trading_client


class AbortTradeException(Exception):
    """Exception signifying a trade abort."""
    pass


BIDS = "bids"
ASKS = "asks"

TARGET_SPREAD = "target_spread"
SPREAD = "spread"
SPREAD_HIGH = "spread_high"
MARKETBUY_EXCHANGE = "marketbuy_exchange"
MARKETSELL_EXCHANGE = "marketsell_exchange"


def get_arb_opportunities_by_orderbook(
        trader1, trader2, spread_low, spread_high):
    """Obtains arbitrage opportunities across two exchanges based on orderbook.

    Uses two real-time api clients to obtain orderbook information, calculate
    the market buy/sell orders within the target_amount's set in the clients.

    Args:
        trader1 (CCXTTrader): The trading client for exchange 1.
        trader2 (CCXTTrader): The trading client for exchange 2.
        spread_low (int): Spread lower boundary in that if the spread crosses
            this, a reverse-arb opportunity exists.
        spread_high (int): Spread upper boundary in that if the spread crosses
            this, a forward-arb opportunity exists.

    Returns:
        dict: A dictionary containing details of the spread opportunity. It
        contains the spread percentage, the exchange client to perform the
        market buy and the exchange to perform the market sell. Ex:

        {
            'target_spread': 10,
            'spread': 2.333,
            'spread_high': True,
            'marketbuy_exchange': client1,
            'marketsell_exchange': client2
        }
    """
    ex1_orderbook = trader1.get_full_orderbook()
    ex2_orderbook = trader2.get_full_orderbook()

    # Exceptions are caught here because we want all the data regardless.
    try:
        ex1_market_buy = trader1.get_adjusted_market_price_from_orderbook(
            ex1_orderbook[ASKS])
    except trading_client.OrderbookException:
        ex1_market_buy = None
    try:
        ex1_market_sell = trader1.get_adjusted_market_price_from_orderbook(
            ex1_orderbook[BIDS])
    except trading_client.OrderbookException:
        ex1_market_sell = None
    try:
        ex2_market_buy = trader2.get_adjusted_market_price_from_orderbook(
            ex2_orderbook[ASKS])
    except trading_client.OrderbookException:
        ex2_market_buy = None
    try:
        ex2_market_sell = trader2.get_adjusted_market_price_from_orderbook(
            ex2_orderbook[BIDS])
    except trading_client.OrderbookException:
        ex2_market_sell = None

    logging.info("%s buy of %s, %s price: %s" %
                 (trader1.exchange_name, trader1.target_amount,
                  trader1.base, ex1_market_buy))
    logging.info("%s buy of %s, %s price: %s" %
                 (trader2.exchange_name, trader2.target_amount,
                  trader2.base, ex2_market_buy))
    logging.info("%s sell of %s, %s price: %s" %
                 (trader1.exchange_name, trader1.target_amount,
                  trader1.base, ex1_market_sell))
    logging.info("%s sell of %s, %s price: %s" %
                 (trader2.exchange_name, trader2.target_amount,
                  trader2.base, ex2_market_sell))

    # Calculate the spreads between exchange 1 and 2.
    # TODO: We need to feed in the fees in order to more accurately calculate
    # the spread.
    ex2msell_ex1mbuy_spread = spreadcalculator.calc_spread(
        ex2_market_sell, ex1_market_buy)
    ex2mbuy_ex1msell_spread = spreadcalculator.calc_spread(
        ex2_market_buy, ex1_market_sell)

    logging.info("Ex2 (%s) sell Ex1 (%s) buy spread: (%s)" %
                 (trader2.exchange_name,
                  trader1.exchange_name,
                  ex2msell_ex1mbuy_spread))
    logging.info("Ex2 (%s) buy Ex1 (%s) sell spread: (%s)" %
                 (trader2.exchange_name,
                  trader1.exchange_name,
                  ex2mbuy_ex1msell_spread))

    # If at or above spread_high, we can perform the forward arbitrage by
    # market selling on exchange 2, market buying on exchange 1.
    # If at or below spread_low, we can perform the reverse arbitrage by market
    # selling on exchange 1, market buying on exchange 2.
    if (ex2msell_ex1mbuy_spread is not None
            and ex2msell_ex1mbuy_spread >= spread_high):
        return {
            TARGET_SPREAD: spread_high,
            SPREAD_HIGH: True,                      # Spread above the high
            SPREAD: ex2msell_ex1mbuy_spread,
            MARKETBUY_EXCHANGE: trader1,
            MARKETSELL_EXCHANGE: trader2
        }
    elif (ex2mbuy_ex1msell_spread is not None
            and ex2mbuy_ex1msell_spread <= spread_low):
        return {
            TARGET_SPREAD: spread_low,
            SPREAD_HIGH: False,                     # Spread below the low
            SPREAD: ex2mbuy_ex1msell_spread,
            MARKETBUY_EXCHANGE: trader2,
            MARKETSELL_EXCHANGE: trader1
        }
    else:
        return None


def execute_arbitrage(opportunity):
    """Execute the arbitrage trade.

    The TradingClient's store information about the ticker, target, and
    exchange details. We verify that the numbers are correct once more
    before execution.

    Args:
        opportunity (dict): A return value of
            get_arb_opportunities_by_orderbook()

    Returns:
        bool: True if succeeded
    """
    # TODO: Add balance checks before execution.
    buy_trading_client = opportunity[MARKETBUY_EXCHANGE]
    sell_trading_client = opportunity[MARKETSELL_EXCHANGE]
    spread_high = opportunity[SPREAD_HIGH]
    target_spread = opportunity[TARGET_SPREAD]

    asks = buy_trading_client.get_full_orderbook()[ASKS]
    bids = sell_trading_client.get_full_orderbook()[BIDS]

    try:
        buy_price = buy_trading_client.get_adjusted_market_price_from_orderbook(asks)
        sell_price = sell_trading_client.get_adjusted_market_price_from_orderbook(bids)

        if spread_high:
            spread = spreadcalculator.calc_spread(sell_price, buy_price)
            execute = spread >= target_spread
        else:
            spread = spreadcalculator.calc_spread(buy_price, sell_price)
            execute = spread <= target_spread

        if not execute:
            message = "Trade aborted. "
            message += "Target spread: %s, " % target_spread
            message += "sell price: %s, " % sell_price
            message += "buy price: %s, " % buy_price
            message += "current spread: %s, " % spread
            message += "calculated spread: %s" % opportunity[SPREAD]
            logging.error(message)
            raise AbortTradeException(message)

        logging.info("Buy price: %s, Sell price %s" % (buy_price, sell_price))
        buy_result = buy_trading_client.execute_market_buy(buy_price)
        logging.info("Buy result: %s" % buy_result)
        executed_buy_amount = buy_result["info"]["executed_amount"]

        sell_result = sell_trading_client.execute_market_sell(
            sell_price,
            float(executed_buy_amount))
        logging.info("Sell result: %s" % sell_result)

    except Exception as exception:
        t = Translator()
        decoded = exception.args[0].encode('utf-8').decode('unicode_escape')
        translation = t.translate(decoded)
        logging.error(translation.text)
        return False
    finally:
        return True
