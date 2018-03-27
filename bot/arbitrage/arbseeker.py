# import spreadcalculator

BIDS = "bids"
ASKS = "asks"

def get_arb_opportunities_by_orderbook(rtapi_ex1, rtapi_ex2, spread_low,
                         spread_high, target_amount):
    """Obtains arbitrage opportunities across two exchanges based on orderbook.

    Uses two real-time api clients to obtain orderbook information, calculate
    the market buy/sell orders within the target_amount.

    Args:
        rtapi_ex1 (object): The real-time api client for exchange 1.
        rtapi_ex2 (object): The real-time api client for exchange 2.
        spread_low (int): Spread lower boundary in that if the spread crosses
            this, a reverse-arb opportunity exists.
        spread_high (int): Spread upper boundary in that if the spread crosses
            this, a forward-arb opportunity exists.
        target_amount (int): The arb target amount to be used in calculating
            the market buy or sell order across orderbooks.

    Returns:
        dict: A dictionary containing details of the spread opportunity. It
        contains the spread percentage, the exchange to perform the market buy
        and the exchange to perform the market sell. Ex:

        {
            'spread': 2.333,
            'marketbuy_exchange': binance,
            'marketsell_exchange': bithumb
        }
    """

    ex1_orderbook = rtapi_ex1.get_full_orderbook()
    ex2_orderbook = rtapi_ex2.get_full_orderbook()

    ex1_market_buy = rtapi_ex1.get_market_price_from_orderbook(
        ex1_orderbook[ASKS], target_amount)
    ex1_market_sell = rtapi_ex1.get_market_price_from_orderbook(
        ex1_orderbook[BIDS], target_amount)
    ex2_market_buy = rtapi_ex2.get_market_price_from_orderbook(
        ex2_orderbook[ASKS], target_amount)
    ex2_market_sell = rtapi_ex2.get_market_price_from_orderbook(
        ex2_orderbook[BIDS], target_amount)

    print("%s buy of %d, %s price: %.2f" %
          (rtapi_ex1.exchange, target_amount, rtapi_ex1.base, ex1_market_buy))
    print("%s buy of %d, %s price: %.2f" %
          (rtapi_ex2.exchange, target_amount, rtapi_ex2.base, ex2_market_buy))
    print("%s sell of %d, %s price: %.2f" %
          (rtapi_ex1.exchange, target_amount, rtapi_ex1.base, ex1_market_sell))
    print("%s sell of %d, %s price: %.2f" %
          (rtapi_ex2.exchange, target_amount, rtapi_ex2.base, ex2_market_sell))

    # Calculate the spreads between exchange 1 and 2.
    # ex1mbuy_ex2msell_spread = spreadcalculator.calc_spread(
    #     ex1_market_buy, ex2_market_sell)
    # ex1msell_ex2mbuy_reversespread = spreadcalculator.calc_spread(
    #     ex1_market_sell, ex2_market_buy)

    ex2msell_ex1mbuy_spread = (ex2_market_sell/ex1_market_buy - 1) * 100
    print("Ex2 sell Ex1 buy spread: " + str(ex2msell_ex1mbuy_spread))

    # If at or above spread_high, we can perform the forward arbitrage by market
    # selling on exchange 2, market buying on exchange 1.
    # If at or below spread_low, we can perform the reverse arbitrage by market
    # selling on exchange 1, market buying on exchange 2.
    if (ex2msell_ex1mbuy_spread >= spread_high):
        return {
            'spread': ex2msell_ex1mbuy_spread,
            'marketbuy_exchange': rtapi_ex1.exchange,
            'marketsell_exchange': rtapi_ex2.exchange
        }
    elif (ex2msell_ex1mbuy_spread <= spread_low):
        return {
            'spread': ex2msell_ex1mbuy_spread,
            'marketbuy_exchange': rtapi_ex2.exchange,
            'marketsell_exchange': rtapi_ex1.exchange
        }
    else:
        return None