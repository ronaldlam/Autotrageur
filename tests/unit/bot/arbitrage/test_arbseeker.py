import pytest

from bot.arbitrage.arbseeker import get_arb_opportunities_by_orderbook
from bot.arbitrage.arbseeker import execute_arbitrage
import bot.arbitrage.spreadcalculator as spreadcalculator
from bot.trader.ccxt_trader import CCXTTrader, OrderbookException


BIDS = "bids"
ASKS = "asks"

TARGET_SPREAD = "target_spread"
SPREAD = "spread"
SPREAD_HIGH = "spread_high"
MARKETBUY_EXCHANGE = "marketbuy_exchange"
MARKETSELL_EXCHANGE = "marketsell_exchange"

TEST_SPREAD = 5


@pytest.fixture(scope='module')
def trader1():
    return CCXTTrader('ETH', 'USD', 'Gemini', 1, 5000)


@pytest.fixture(scope='module')
def trader2():
    return CCXTTrader('ETH', 'KRW', 'Bithumb', 1, 5000000)


@pytest.mark.parametrize(
    "spread_low, spread_high, has_bad_orderbook", [
        (0, 4, False),
        (5, 10, False),
        (2, 2, False),
        (6, 6, False),
        (2, 7, False),
        (0, 4, True),
        (5, 10, True),
        (2, 2, True),
        (6, 6, True),
        (2, 7, True),
        (None, 4, False), # Still triggers correctly, first calculated
        pytest.param(None, 6, False,
            marks=pytest.mark.xfail(strict=True, raises=TypeError)),
        pytest.param(4, None, False,
            marks=pytest.mark.xfail(strict=True, raises=TypeError)),
        pytest.param(6, None, False,
            marks=pytest.mark.xfail(strict=True, raises=TypeError)),
    ]
)
def test_get_opportunities(
        mocker, trader1, trader2, spread_low, spread_high, has_bad_orderbook):
    if has_bad_orderbook:
        mocker.patch.object(
            trader1,
            'get_adjusted_market_price_from_orderbook',
            side_effect=OrderbookException)
        mocker.patch.object(
            trader2,
            'get_adjusted_market_price_from_orderbook',
            side_effect=OrderbookException)
    else:
        mocker.patch.object(
            trader1,
            'get_adjusted_market_price_from_orderbook')
        mocker.patch.object(
            trader2,
            'get_adjusted_market_price_from_orderbook')

    mocker.patch.object(trader1, 'get_full_orderbook')
    mocker.patch.object(trader1, 'exchange_name')
    mocker.patch.object(trader1, 'target_amount')
    mocker.patch.object(trader1, 'base')

    mocker.patch.object(trader2, 'get_full_orderbook')
    mocker.patch.object(trader2, 'exchange_name')
    mocker.patch.object(trader2, 'target_amount')
    mocker.patch.object(trader2, 'base')

    mocker.patch.object(spreadcalculator, 'calc_spread')
    spreadcalculator.calc_spread.return_value = TEST_SPREAD

    result = get_arb_opportunities_by_orderbook(
        trader1, trader2, spread_low, spread_high)

    trader1.get_full_orderbook.assert_called_once()
    trader2.get_full_orderbook.assert_called_once()
    assert(trader1.get_adjusted_market_price_from_orderbook.call_count == 2)
    assert(trader2.get_adjusted_market_price_from_orderbook.call_count == 2)

    if (TEST_SPREAD >= spread_high):
        target_spread = spread_high
        is_high = True
    elif (TEST_SPREAD <= spread_low):
        target_spread = spread_low
        is_high = False
    else:
        assert(result == None)
        return

    assert(result[TARGET_SPREAD] == target_spread)
    assert(result[SPREAD_HIGH] == is_high)
    assert(result[SPREAD] == 5)


@pytest.mark.parametrize(
    "target_spread, spread_high, spread", [
        (5, True, 6),
        (5, False, 4)
    ]
)
def test_execute_arbitrage(
        mocker, trader1, trader2, target_spread, spread_high, spread):
    mocker.patch.object(trader1, 'get_full_orderbook')
    mocker.patch.object(trader1, 'get_adjusted_market_price_from_orderbook')
    mocker.patch.object(trader1, 'execute_market_buy')
    trader1.execute_market_buy.return_value = {
        "info": {
            "executed_amount": TEST_SPREAD
        }
    }

    mocker.patch.object(trader2, 'get_full_orderbook')
    mocker.patch.object(trader2, 'get_adjusted_market_price_from_orderbook')
    mocker.patch.object(trader2, 'execute_market_sell')

    mocker.patch.object(spreadcalculator, 'calc_spread')
    spreadcalculator.calc_spread.return_value = spread

    opportunity = {
        TARGET_SPREAD: target_spread,
        SPREAD_HIGH: spread_high,
        SPREAD: spread,
        MARKETBUY_EXCHANGE: trader1,
        MARKETSELL_EXCHANGE: trader2
    }

    assert(execute_arbitrage(opportunity))

    trader1.get_full_orderbook.assert_called_once()
    trader1.get_adjusted_market_price_from_orderbook.assert_called_once()
    trader1.execute_market_buy.assert_called_once()

    trader2.get_full_orderbook.assert_called_once()
    trader2.get_adjusted_market_price_from_orderbook.assert_called_once()
    trader2.execute_market_sell.assert_called_once()


@pytest.mark.parametrize(
    "target_spread, spread_high, spread", [
        (5, True, 6),
        (3, False, 2)
    ]
)
def test_abort_arbitrage(
        mocker, trader1, trader2, target_spread, spread_high, spread):
    mocker.patch.object(trader1, 'get_full_orderbook')
    mocker.patch.object(trader1, 'get_adjusted_market_price_from_orderbook')
    mocker.patch.object(trader1, 'execute_market_buy')
    trader1.execute_market_buy.return_value = {
        "info": {
            "executed_amount": TEST_SPREAD
        }
    }

    mocker.patch.object(trader2, 'get_full_orderbook')
    mocker.patch.object(trader2, 'get_adjusted_market_price_from_orderbook')
    mocker.patch.object(trader2, 'execute_market_sell')

    mocker.patch.object(spreadcalculator, 'calc_spread')
    spreadcalculator.calc_spread.return_value = 4

    opportunity = {
        TARGET_SPREAD: target_spread,
        SPREAD_HIGH: spread_high,
        SPREAD: spread,
        MARKETBUY_EXCHANGE: trader1,
        MARKETSELL_EXCHANGE: trader2
    }

    assert not (execute_arbitrage(opportunity))

    trader1.get_full_orderbook.assert_called_once()
    trader1.get_adjusted_market_price_from_orderbook.assert_called_once()
    assert(trader1.execute_market_buy.call_count == 0)

    trader2.get_full_orderbook.assert_called_once()
    trader2.get_adjusted_market_price_from_orderbook.assert_called_once()
    assert(trader2.execute_market_sell.call_count == 0)


def test_dead_opportunity():
    with pytest.raises(TypeError):
        execute_arbitrage(None)