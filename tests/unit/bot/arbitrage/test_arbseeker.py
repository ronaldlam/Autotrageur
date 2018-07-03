from ccxt import NetworkError
import pytest

from bot.arbitrage.arbseeker import get_spreads_by_ob, SpreadOpportunity
import bot.arbitrage.spreadcalculator as spreadcalculator
from bot.trader.ccxt_trader import CCXTTrader, OrderbookException


BIDS = "bids"
ASKS = "asks"

TARGET_SPREAD = "target_spread"
SPREAD = "spread"
SPREAD_OPP_TYPE = "spread_opp_type"
MARKETBUY_EXCHANGE = "marketbuy_exchange"
MARKETSELL_EXCHANGE = "marketsell_exchange"

FAKE_EXECUTED_AMOUNT = 999
TEST_SPREAD = 5
TEST_BUY_PRICE = 10
TEST_SELL_PRICE = 5


@pytest.fixture(scope='module')
def buy_trader():
    return CCXTTrader('ETH', 'USD', 'Gemini', 1)


@pytest.fixture(scope='module')
def sell_trader():
    return CCXTTrader('ETH', 'KRW', 'Bithumb', 1)


@pytest.mark.parametrize(
    "has_bad_orderbook", [
        True, False
    ]
)
def test_get_spreads_by_ob(
        mocker, buy_trader, sell_trader, has_bad_orderbook):
    if has_bad_orderbook:
        mocker.patch.object(
            buy_trader,
            'get_prices_from_orderbook',
            side_effect=OrderbookException)
        mocker.patch.object(
            sell_trader,
            'get_prices_from_orderbook',
            side_effect=OrderbookException)
    else:
        mocker.patch.object(
            buy_trader,
            'get_prices_from_orderbook')
        mocker.patch.object(
            sell_trader,
            'get_prices_from_orderbook')

    mocker.patch.object(buy_trader, 'get_full_orderbook')
    mocker.patch.object(buy_trader, 'exchange_name')
    mocker.patch.object(buy_trader, 'quote_target_amount')
    mocker.patch.object(buy_trader, 'base')

    mocker.patch.object(sell_trader, 'get_full_orderbook')
    mocker.patch.object(sell_trader, 'exchange_name')
    mocker.patch.object(sell_trader, 'quote_target_amount')
    mocker.patch.object(sell_trader, 'base')

    mocker.patch.object(spreadcalculator, 'calc_fixed_spread')
    spreadcalculator.calc_fixed_spread.return_value = TEST_SPREAD

    result = get_spreads_by_ob(buy_trader, sell_trader)

    buy_trader.get_full_orderbook.assert_called_once()
    sell_trader.get_full_orderbook.assert_called_once()
    assert(buy_trader.get_prices_from_orderbook.call_count == 2)
    assert(sell_trader.get_prices_from_orderbook.call_count == 2)
    assert isinstance(result, SpreadOpportunity)


# class TestExecuteArbitrage:
#     trade_metadata = None

#     def __setup_trade_data(self, buy_trader, sell_trader):
#         buy_trader.execute_market_buy.return_value = {
#             "info": {
#                 "executed_amount": FAKE_EXECUTED_AMOUNT
#             }
#         }

#         if not self.trade_metadata:
#             self.trade_metadata = {
#                 'buy_price': TEST_BUY_PRICE,
#                 'sell_price': TEST_SELL_PRICE,
#                 'buy_trader': buy_trader,
#                 'sell_trader': sell_trader
#             }

#     def test_execute_arbitrage(self, mocker, buy_trader, sell_trader):
#         # buy_trader should be the buyer, sell_trader should be the seller.
#         mocker.patch.object(buy_trader, 'execute_market_buy')
#         mocker.patch.object(buy_trader, 'execute_market_sell')
#         mocker.patch.object(sell_trader, 'execute_market_sell')
#         mocker.patch.object(sell_trader, 'execute_market_buy')

#         self.__setup_trade_data(buy_trader, sell_trader)

#         assert(execute_arbitrage(self.trade_metadata))

#         buy_trader.execute_market_buy.assert_called_once()
#         buy_trader.execute_market_buy.assert_called_with(self.trade_metadata['buy_price'])
#         assert buy_trader.execute_market_sell.call_count == 0

#         sell_trader.execute_market_sell.assert_called_once()
#         sell_trader.execute_market_sell.assert_called_with(self.trade_metadata['sell_price'],
#                 buy_trader.execute_market_buy.return_value['info']['executed_amount'])
#         assert sell_trader.execute_market_buy.call_count == 0

#     @pytest.mark.parametrize(
#         "buy_network_err", [
#             True, False
#         ]
#     )
#     def test_execute_arbitrage_networkerror(self, mocker, buy_trader, sell_trader, buy_network_err):
#         if buy_network_err:
#             mocker.patch.object(buy_trader, 'execute_market_buy',
#                                 side_effect=NetworkError)
#         else:
#             mocker.patch.object(buy_trader, 'execute_market_buy')
#             mocker.patch.object(sell_trader, 'execute_market_sell',
#                                 side_effect=NetworkError)

#         self.__setup_trade_data(buy_trader, sell_trader)

#         result = execute_arbitrage(self.trade_metadata)
#         assert result is False

#     def test_dead_opportunity(self):
#         with pytest.raises(TypeError):
#             execute_arbitrage(None)
