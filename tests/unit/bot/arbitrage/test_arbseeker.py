from ccxt import NetworkError
import pytest

from bot.arbitrage.arbseeker import (get_spreads_by_ob,
                                     execute_buy,
                                     execute_sell,
                                     SpreadOpportunity)
import bot.arbitrage.spreadcalculator as spreadcalculator
from bot.trader.ccxt_trader import CCXTTrader, OrderbookException
from libs.utilities import num_to_decimal


BIDS = "bids"
ASKS = "asks"

TEST_SPREAD = num_to_decimal(5)
TEST_BUY_PRICE = num_to_decimal(10)
TEST_SELL_PRICE = num_to_decimal(5)
TEST_EXEC_AMOUNT = num_to_decimal(1.2345678)
TEST_GEMINI_TAKER_FEE = num_to_decimal(0.01)
TEST_BITHUMB_TAKER_FEE = num_to_decimal(0.0015)
TEST_GEMINI_BUY_INCL_FEE = False
TEST_BITHUMB_BUY_INCL_FEE = True
TEST_FAKE_BUY_RESULT = {
    'fake_buy': 'result'
}
TEST_FAKE_SELL_RESULT = {
    'fake_sell': 'result'
}

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
            'get_adjusted_market_price_from_orderbook',
            side_effect=OrderbookException)
        mocker.patch.object(
            sell_trader,
            'get_adjusted_market_price_from_orderbook',
            side_effect=OrderbookException)
    else:
        mocker.patch.object(
            buy_trader,
            'get_adjusted_market_price_from_orderbook',
            return_value=TEST_BUY_PRICE)
        mocker.patch.object(
            sell_trader,
            'get_adjusted_market_price_from_orderbook',
            return_value=TEST_SELL_PRICE)

    mocker.patch.object(buy_trader, 'get_full_orderbook')
    mocker.patch.object(buy_trader, 'exchange_name')
    mocker.patch.object(buy_trader, 'quote_target_amount')
    mocker.patch.object(buy_trader, 'base')
    mocker.patch.object(
        buy_trader, 'get_taker_fee', return_value=TEST_GEMINI_TAKER_FEE)
    mocker.patch.object(
        buy_trader, 'get_buy_target_includes_fee', return_value=False)

    mocker.patch.object(sell_trader, 'get_full_orderbook')
    mocker.patch.object(sell_trader, 'exchange_name')
    mocker.patch.object(sell_trader, 'quote_target_amount')
    mocker.patch.object(sell_trader, 'base')
    mocker.patch.object(
        sell_trader, 'get_taker_fee', return_value=TEST_BITHUMB_TAKER_FEE)
    mocker.patch.object(
        sell_trader, 'get_buy_target_includes_fee', return_value=True)

    mocker.patch.object(spreadcalculator, 'calc_fixed_spread')
    spreadcalculator.calc_fixed_spread.return_value = TEST_SPREAD

    result = get_spreads_by_ob(buy_trader, sell_trader)

    # Validate mocked calls
    buy_trader.get_full_orderbook.assert_called_once()
    sell_trader.get_full_orderbook.assert_called_once()
    assert(buy_trader.get_adjusted_market_price_from_orderbook.call_count == 2)
    assert(sell_trader.get_adjusted_market_price_from_orderbook.call_count == 2)
    assert(spreadcalculator.calc_fixed_spread.call_count == 2)      # pylint: disable=E1101

    # Validate the SpreadOpportunity instance
    assert isinstance(result, SpreadOpportunity)
    assert hasattr(result, 'e1_spread')
    assert hasattr(result, 'e2_spread')
    assert hasattr(result, 'e1_buy')
    assert hasattr(result, 'e2_buy')
    assert hasattr(result, 'e1_sell')
    assert hasattr(result, 'e2_sell')

    # Validate spreadcalculator calls.
    if has_bad_orderbook:
        assert spreadcalculator.calc_fixed_spread.call_args_list == [       # pylint: disable=E1101
            mocker.call(None, None, TEST_BITHUMB_TAKER_FEE, TEST_GEMINI_TAKER_FEE, True),
            mocker.call(None, None, TEST_GEMINI_TAKER_FEE, TEST_BITHUMB_TAKER_FEE, False)
        ]
    else:
        assert spreadcalculator.calc_fixed_spread.call_args_list == [       # pylint: disable=E1101
            mocker.call(TEST_SELL_PRICE, TEST_BUY_PRICE, TEST_BITHUMB_TAKER_FEE, TEST_GEMINI_TAKER_FEE, True),
            mocker.call(TEST_BUY_PRICE, TEST_SELL_PRICE, TEST_GEMINI_TAKER_FEE, TEST_BITHUMB_TAKER_FEE, False)
        ]


def test_execute_buy(mocker, buy_trader):
    mocker.patch.object(buy_trader, 'execute_market_buy', return_value=TEST_FAKE_BUY_RESULT)
    result = execute_buy(buy_trader, TEST_BUY_PRICE)

    buy_trader.execute_market_buy.assert_called_once_with(TEST_BUY_PRICE)
    assert result is TEST_FAKE_BUY_RESULT


def test_execute_sell(mocker, buy_trader):
    mocker.patch.object(buy_trader, 'execute_market_sell', return_value=TEST_FAKE_SELL_RESULT)
    result = execute_sell(buy_trader, TEST_SELL_PRICE, TEST_EXEC_AMOUNT)

    buy_trader.execute_market_sell.assert_called_once_with(TEST_SELL_PRICE, TEST_EXEC_AMOUNT)
    assert result is TEST_FAKE_SELL_RESULT
