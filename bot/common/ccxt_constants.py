"""Exchange configuration constants."""
API_KEY = 'api_key'
API_SECRET = 'api_secret'
PASSWORD = 'password'

"""Extended ccxt exchanges constants."""
BUY_SIDE = 'buy'
SELL_SIDE = 'sell'
ORDER_TYPE_MARKET = 'market'
ORDER_TYPE_LIMIT = 'limit'

"""Unified CCXT API function names.
From https://github.com/ccxt/ccxt/wiki/Manual#overview:
    'loadMarkets',
    'fetchBalance',
    'fetchMarkets',
    'createOrder',
    'fetchCurrencies',
    'cancelOrder',
    'fetchTicker',
    'fetchOrder',
    'fetchTickers',
    'fetchOrders',
    'fetchOrderBook',
    'fetchOpenOrders',
    'fetchOHLCV',
    'fetchClosedOrders',
    'fetchTrades',
    'fetchMyTrades',
    'deposit',
    'withdraw'
"""
UNIFIED_FUNCTION_NAMES = [
    'fetch_markets',
    'fetch_balance',
    'fetch_order_book',
    'fetch_tickers',
    'fetch_ticker',
    'fetch_trades',
    'fetch_order',
    'create_order',
    'cancel_order',
    'withdraw'
]
