# pylint: disable=E1101
import pytest

import bot.arbitrage.spreadcalculator as spreadcalculator
from bot.arbitrage.arbseeker import (E1_BUY, E1_SELL, E2_BUY, E2_SELL,
                                     AsymmetricConvertOpError, PriceEntry,
                                     SpreadOpportunity, _convert_sell_amounts,
                                     _form_price_data, execute_buy,
                                     execute_sell, get_spreads_by_ob)
from bot.trader.ccxt_trader import CCXTTrader, OrderbookException, PricePair
from libs.constants.ccxt_constants import BUY_SIDE, SELL_SIDE
from libs.utilities import num_to_decimal

BIDS = "bids"
ASKS = "asks"

# Price Pairs.
TEST_BUY_PRICE_USD = num_to_decimal(1)
TEST_BUY_PRICE_KRW = num_to_decimal(1000)
TEST_SELL_PRICE_USD = num_to_decimal(5)
TEST_SELL_PRICE_KRW = num_to_decimal(5000)
TEST_BUY_PRICE_PAIR = PricePair(TEST_BUY_PRICE_USD, TEST_BUY_PRICE_KRW)
TEST_SELL_PRICE_PAIR = PricePair(TEST_SELL_PRICE_USD, TEST_SELL_PRICE_KRW)

TEST_SPREAD = num_to_decimal(5)
TEST_EXEC_AMOUNT = num_to_decimal(1.2345678)
TEST_GEMINI_TAKER_FEE = num_to_decimal(0.01)
TEST_BITHUMB_TAKER_FEE = num_to_decimal(0.0015)
TEST_GEMINI_BUY_INCL_FEE = False
TEST_BITHUMB_BUY_INCL_FEE = True
TEST_FAKE_BUY_RESULT = {
    'fake_buy': 'result',
    'post_fee_base': 1.1,
    'post_fee_quote': 1.1,
}
TEST_FAKE_SELL_RESULT = {
    'fake_sell': 'result',
    'pre_fee_base': 1.1,
    'post_fee_quote': 1.1,
}


@pytest.fixture(scope='module')
def buy_trader():
    return CCXTTrader('ETH', 'USD', 'Gemini', 'e1', 1)


@pytest.fixture(scope='module')
def sell_trader():
    return CCXTTrader('ETH', 'KRW', 'Bithumb', 'e2', 1)


@pytest.mark.parametrize('t2_convert_op', [
    True,
    None
])
@pytest.mark.parametrize('t1_convert_op', [
    True,
    None
])
@pytest.mark.parametrize('t1_conversion_needed', [True, False])
@pytest.mark.parametrize('t2_conversion_needed', [True, False])
def test_convert_sell_amounts(mocker, t1_convert_op, t2_convert_op,
                              t1_conversion_needed, t2_conversion_needed):
    trader1 = mocker.Mock()
    trader2 = mocker.Mock()
    mocker.patch.object(trader1, 'quote_target_amount')
    mocker.patch.object(trader2, 'quote_target_amount')
    mocker.patch.object(trader1, 'conversion_needed', t1_conversion_needed)
    mocker.patch.object(trader2, 'conversion_needed', t2_conversion_needed)

    # Mocks a convert function if convert_op is present.
    if t1_convert_op:
        mocker.patch.object(trader1, 'sell_side_convert_op')
    else:
        mocker.patch.object(trader1, 'sell_side_convert_op', t1_convert_op)
    if t2_convert_op:
        mocker.patch.object(trader1, 'sell_side_convert_op')
    else:
        mocker.patch.object(trader1, 'sell_side_convert_op', t2_convert_op)

    if trader1.sell_side_convert_op and trader2.sell_side_convert_op:
        result = _convert_sell_amounts(trader1, trader2)

        if t1_conversion_needed:
            trader1.sell_side_convert_op.assert_called_once_with(
               trader2.quote_target_amount,
               trader1.forex_ratio)
            trader2.sell_side_convert_op.assert_called_once_with(
               trader1.quote_target_amount,
               trader1.forex_ratio)
        else:
            trader1.sell_side_convert_op.assert_called_once_with(
               trader2.quote_target_amount,
               trader2.forex_ratio)
            trader2.sell_side_convert_op.assert_called_once_with(
               trader1.quote_target_amount,
               trader2.forex_ratio)

        assert result == (trader2.sell_side_convert_op.return_value,
                          trader1.sell_side_convert_op.return_value)

    elif not trader1.sell_side_convert_op and not trader2.sell_side_convert_op:
        result = _convert_sell_amounts(trader1, trader2)

        assert result == (trader1.quote_target_amount, trader2.quote_target_amount)
    else:
        with pytest.raises(AsymmetricConvertOpError):
            _convert_sell_amounts(trader1, trader2)


def test_form_price_data(mocker):
    trader1 = mocker.Mock()
    trader2 = mocker.Mock()
    ex1_orderbook = {
        ASKS: mocker.Mock(),
        BIDS: mocker.Mock()
    }
    ex2_orderbook = {
        ASKS: mocker.Mock(),
        BIDS: mocker.Mock()
    }
    mock_t1_converted_amount = mocker.Mock()
    mock_t2_converted_amount = mocker.Mock()
    mocker.patch('bot.arbitrage.arbseeker._convert_sell_amounts',
        return_value=(mock_t1_converted_amount, mock_t2_converted_amount))

    result = _form_price_data(trader1, trader2, ex1_orderbook, ex2_orderbook)

    assert result == [
        PriceEntry(
            price_type=E1_BUY,
            side=BUY_SIDE,
            trader=trader1,
            quote_target_amount=trader1.quote_target_amount,
            usd_target_amount=trader1.usd_target_amount,
            bids_or_asks=ex1_orderbook[ASKS]),
        PriceEntry(
            price_type=E1_SELL,
            side=SELL_SIDE,
            trader=trader1,
            quote_target_amount=mock_t2_converted_amount,
            usd_target_amount=trader2.usd_target_amount,
            bids_or_asks=ex1_orderbook[BIDS]),
        PriceEntry(
            price_type=E2_BUY,
            side=BUY_SIDE,
            trader=trader2,
            quote_target_amount=trader2.quote_target_amount,
            usd_target_amount=trader2.usd_target_amount,
            bids_or_asks=ex2_orderbook[ASKS]),
        PriceEntry(
            price_type=E2_SELL,
            side=SELL_SIDE,
            trader=trader2,
            quote_target_amount=mock_t1_converted_amount,
            usd_target_amount=trader1.usd_target_amount,
            bids_or_asks=ex2_orderbook[BIDS]),
    ]

@pytest.mark.parametrize(
    "has_bad_orderbook", [
        True, False
    ]
)
def test_get_spreads_by_ob(
        mocker, buy_trader, sell_trader, has_bad_orderbook):
    mock_ex1_orderbook = mocker.MagicMock()
    mock_ex2_orderbook = mocker.MagicMock()
    mock_price_entries = [
        PriceEntry(
            price_type=E1_BUY,
            side=BUY_SIDE,
            trader=buy_trader,
            quote_target_amount=mocker.Mock(),
            usd_target_amount=mocker.Mock(),
            bids_or_asks=mock_ex1_orderbook[ASKS]),
        PriceEntry(
            price_type=E1_SELL,
            side=SELL_SIDE,
            trader=buy_trader,
            quote_target_amount=mocker.Mock(),
            usd_target_amount=mocker.Mock(),
            bids_or_asks=mock_ex1_orderbook[BIDS]),
        PriceEntry(
            price_type=E2_BUY,
            side=BUY_SIDE,
            trader=sell_trader,
            quote_target_amount=mocker.Mock(),
            usd_target_amount=mocker.Mock(),
            bids_or_asks=mock_ex2_orderbook[ASKS]),
        PriceEntry(
            price_type=E2_SELL,
            side=SELL_SIDE,
            trader=sell_trader,
            quote_target_amount=mocker.Mock(),
            usd_target_amount=mocker.Mock(),
            bids_or_asks=mock_ex2_orderbook[BIDS]),
    ]

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
            'get_prices_from_orderbook',
            return_value=TEST_BUY_PRICE_PAIR)
        mocker.patch.object(
            sell_trader,
            'get_prices_from_orderbook',
            return_value=TEST_SELL_PRICE_PAIR)

    mocker.patch.object(buy_trader, 'get_full_orderbook', return_value=mock_ex1_orderbook)
    mocker.patch.object(buy_trader, 'exchange_name')
    mocker.patch.object(buy_trader, 'quote_target_amount')
    mocker.patch.object(buy_trader, 'base')
    mocker.patch.object(
        buy_trader, 'get_taker_fee', return_value=TEST_GEMINI_TAKER_FEE)
    mocker.patch.object(
        buy_trader, 'get_buy_target_includes_fee', return_value=False)

    mocker.patch.object(sell_trader, 'get_full_orderbook', return_value=mock_ex2_orderbook)
    mocker.patch.object(sell_trader, 'exchange_name')
    mocker.patch.object(sell_trader, 'quote_target_amount')
    mocker.patch.object(sell_trader, 'base')
    mocker.patch.object(
        sell_trader, 'get_taker_fee', return_value=TEST_BITHUMB_TAKER_FEE)
    mocker.patch.object(
        sell_trader, 'get_buy_target_includes_fee', return_value=True)

    mock_form_price_data = mocker.patch(
        'bot.arbitrage.arbseeker._form_price_data', return_value=mock_price_entries)

    # Stop the test pre-emptively if has_bad_orderbook, as an
    # exception should be raised.
    if has_bad_orderbook:
        with pytest.raises(OrderbookException):
            result = get_spreads_by_ob(buy_trader, sell_trader)
            spreadcalculator.calc_fixed_spread.assert_not_called()
            assert result is None
    else:
        mocker.patch.object(spreadcalculator, 'calc_fixed_spread')
        spreadcalculator.calc_fixed_spread.return_value = TEST_SPREAD

        result = get_spreads_by_ob(buy_trader, sell_trader)

        # Validate mocked calls
        buy_trader.get_full_orderbook.assert_called_once()
        sell_trader.get_full_orderbook.assert_called_once()
        mock_form_price_data.assert_called_once_with(buy_trader, sell_trader,
            mock_ex1_orderbook, mock_ex2_orderbook)
        assert(buy_trader.get_prices_from_orderbook.call_count == 2)
        assert(sell_trader.get_prices_from_orderbook.call_count == 2)
        assert(spreadcalculator.calc_fixed_spread.call_count == 2)

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
            assert spreadcalculator.calc_fixed_spread.call_args_list == [
                mocker.call(None, None, TEST_BITHUMB_TAKER_FEE, TEST_GEMINI_TAKER_FEE, True),
                mocker.call(None, None, TEST_GEMINI_TAKER_FEE, TEST_BITHUMB_TAKER_FEE, False)
            ]
        else:
            assert spreadcalculator.calc_fixed_spread.call_args_list == [
                mocker.call(TEST_SELL_PRICE_USD, TEST_BUY_PRICE_USD, TEST_BITHUMB_TAKER_FEE, TEST_GEMINI_TAKER_FEE, True),
                mocker.call(TEST_BUY_PRICE_USD, TEST_SELL_PRICE_USD, TEST_GEMINI_TAKER_FEE, TEST_BITHUMB_TAKER_FEE, False)
            ]


def test_execute_buy(mocker, buy_trader):
    mocker.patch.object(buy_trader, 'execute_market_buy', return_value=TEST_FAKE_BUY_RESULT)
    result = execute_buy(buy_trader, TEST_BUY_PRICE_USD)

    buy_trader.execute_market_buy.assert_called_once_with(TEST_BUY_PRICE_USD)
    assert result is TEST_FAKE_BUY_RESULT


def test_execute_sell(mocker, buy_trader):
    mocker.patch.object(buy_trader, 'execute_market_sell', return_value=TEST_FAKE_SELL_RESULT)
    result = execute_sell(buy_trader, TEST_SELL_PRICE_USD, TEST_EXEC_AMOUNT)

    buy_trader.execute_market_sell.assert_called_once_with(TEST_SELL_PRICE_USD, TEST_EXEC_AMOUNT)
    assert result is TEST_FAKE_SELL_RESULT
