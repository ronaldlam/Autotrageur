from decimal import Decimal

import pytest

from bot.arbitrage.fcf.trade_chunker import FCFTradeChunker
from fp_libs.constants.decimal_constants import ZERO

MAX_TRADE_SIZE = Decimal('1000')

@pytest.fixture(scope='module')
def fcf_trade_chunker():
    return FCFTradeChunker(MAX_TRADE_SIZE)


def test_init():
    result = FCFTradeChunker(MAX_TRADE_SIZE)
    assert result._max_trade_size == MAX_TRADE_SIZE
    assert result._target == None
    assert result._current_trade_size == ZERO
    assert result.trade_completed == True


@pytest.mark.parametrize(
    'target, current_trade_size, post_fee_cost, min_trade_size, '
    'expected_trade_completion', [
        (Decimal('5000'), Decimal('4000'), Decimal('1000'), Decimal('3'), True),
        (Decimal('5000'), Decimal('4000'), Decimal('997'), Decimal('3'), False),
        (Decimal('5000'), Decimal('3997'), Decimal('1000'), Decimal('3'), False),
        (Decimal('5003'), Decimal('4000'), Decimal('1000'), Decimal('3'), False),
        (Decimal('5002'), Decimal('4000'), Decimal('1000'), Decimal('3'), True),
        (Decimal('500'), Decimal('0'), Decimal('497.345'), Decimal('7.234'), True),
        (Decimal('500'), Decimal('0'), Decimal('481.345'), Decimal('7.234'), False),
        (Decimal('500'), Decimal('0'), Decimal('541.345'), Decimal('7.234'), True),
    ])
def test_finalize_trade(
        mocker, fcf_trade_chunker, target, current_trade_size, post_fee_cost,
        min_trade_size, expected_trade_completion):
    mocker.patch.object(fcf_trade_chunker, '_target', target)
    mocker.patch.object(fcf_trade_chunker, '_current_trade_size', current_trade_size)

    fcf_trade_chunker.finalize_trade(post_fee_cost, min_trade_size)

    assert fcf_trade_chunker.trade_completed == expected_trade_completion


@pytest.mark.parametrize('target, current_trade_size, expected_result', [
    (Decimal('5000'), Decimal('4000'), Decimal('1000')),
    (Decimal('5000'), Decimal('3000'), Decimal('1000')),
    (Decimal('5000'), Decimal('4500'), Decimal('500')),
    (Decimal('500'), Decimal('400'), Decimal('100')),
    (Decimal('500'), Decimal('0'), Decimal('500')),
    (Decimal('500.52'), Decimal('0'), Decimal('500.52')),
])
def test_get_next_trade(
        mocker, fcf_trade_chunker, target, current_trade_size, expected_result):
    mocker.patch.object(fcf_trade_chunker, '_target', target)
    mocker.patch.object(fcf_trade_chunker, '_current_trade_size', current_trade_size)

    result = fcf_trade_chunker.get_next_trade()

    assert result == expected_result


def test_reset(mocker, fcf_trade_chunker):
    mock_target = mocker.Mock()
    fcf_trade_chunker.reset(mock_target)
    assert fcf_trade_chunker._target == mock_target
    assert fcf_trade_chunker._current_trade_size == ZERO
    assert fcf_trade_chunker.trade_completed == False
