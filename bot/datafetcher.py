import ccxt

def dump(*args):
    print(' '.join([str(arg) for arg in args]))

# if __name__ == "__main__":
#     print("------------------ Sample program with BTC/KRW BTC/USD spread on bithumb and bitfinex ------------------")
#     btckrw_last_price_bithumb = fetch_last_price(ccxt.bithumb(), 'BTC/KRW')
#     btcusd_last_price_bitfinex = fetch_last_price(ccxt.bitfinex(), 'BTC/USD')

#     dump('bithumb',
#         'Last traded at:\n',
#         btckrw_last_price_bithumb)

#     dump('bitfinex',
#         'Last traded at:\n',
#         btcusd_last_price_bitfinex)

#     calc_krwusd_spread(btckrw_last_price_bithumb, btcusd_last_price_bitfinex)