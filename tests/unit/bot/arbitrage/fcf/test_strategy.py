import uuid
from decimal import Decimal
from unittest.mock import Mock, MagicMock

import pytest
from ccxt import NetworkError

import bot.arbitrage.arbseeker as arbseeker
from bot.arbitrage.fcf.strategy import (FCFStrategy, InsufficientCryptoBalance,
                                        TradeMetadata)
from bot.arbitrage.fcf.target_tracker import FCFTargetTracker
from bot.arbitrage.fcf.trade_chunker import FCFTradeChunker
from bot.common.enums import Momentum
from bot.trader.ccxt_trader import CCXTTrader, OrderbookException

FAKE_CONFIG_UUID = str(uuid.uuid4())


@pytest.fixture(scope='module')
def fcf_strategy():
    return FCFStrategy(
        strategy_state=MagicMock(),
        manager=MagicMock(),
        max_trade_size=Mock(),
        spread_min=Mock(),
        vol_min=Mock())


@pytest.mark.parametrize(
    'vol_min, spread, h_max, from_balance, result', [
        (Decimal('1000'), Decimal('4'), Decimal('2'), Decimal('1000'),
            [(Decimal('5'), Decimal('1000'))]),  # spread + spread_min > h_max, vol_min == from_balance
        (Decimal('2000'), Decimal('2'), Decimal('3'), Decimal('1000'),
            [(Decimal('3'), Decimal('1000'))]),  # spread + spread_min == h_max, vol_min > from_balance
        (Decimal('2000'), Decimal('1.5'), Decimal('3'), Decimal('1000'),
            [(Decimal('3'), Decimal('1000'))]),  # spread + spread_min < h_max, vol_min > from_balance
        (Decimal('1000'), Decimal('2'), Decimal('3'), Decimal('2000'),
            [(Decimal('3'), Decimal('2000'))]),  # spread + spread_min == h_max, vol_min < from_balance
        (Decimal('1000'), Decimal('2'), Decimal('4'), Decimal('2000'),
            [(Decimal('3'), Decimal('1000')), (Decimal('4'), Decimal('2000'))]),
        (Decimal('500'), Decimal('2'), Decimal('5'), Decimal('2000'),
            [(Decimal('3'), Decimal('500')), (Decimal('4'), Decimal('1000')), (Decimal('5'), Decimal('2000'))]),
        (Decimal('2000'), Decimal('2'), Decimal('5'), Decimal('2000'),
            [(Decimal('3'), Decimal('2000')), (Decimal('4'), Decimal('2000')), (Decimal('5'), Decimal('2000'))]),
        (Decimal('1000'), Decimal('-3'), Decimal('0'), Decimal('1000'),
            [(Decimal('-2'), Decimal('1000')), (Decimal('-1'), Decimal('1000')), (Decimal('0'), Decimal('1000'))]),
        (Decimal('500'), Decimal('-3'), Decimal('0'), Decimal('2000'),
            [(Decimal('-2'), Decimal('500')), (Decimal('-1'), Decimal('1000')), (Decimal('0'), Decimal('2000'))]),
    ])
def test_calc_targets(mocker, fcf_strategy, vol_min, spread, h_max,
                      from_balance, result):
    mocker.patch.object(
        fcf_strategy, '_spread_min', Decimal('1'), create=True)
    mocker.patch.object(
        fcf_strategy, '_vol_min', vol_min, create=True)
    targets = fcf_strategy._FCFStrategy__calc_targets(
        spread, h_max, from_balance)
    assert targets == result


@pytest.mark.parametrize(
    'min_base_buy, min_base_sell, buy_price, buy_quote_target, expected_result', [
        (Decimal('0.1'), Decimal('0.1'), Decimal('100'), Decimal('10'), False),
        (Decimal('0.1'), Decimal('0.1'), Decimal('100'), Decimal('11'), True),
        (Decimal('0.1'), Decimal('0.1'), Decimal('100'), Decimal('9'), False),
        (Decimal('0.1'), Decimal('0.05'), Decimal('100'), Decimal('10'), False),
        (Decimal('0.1'), Decimal('0.05'), Decimal('100'), Decimal('11'), True),
        (Decimal('0.1'), Decimal('0.05'), Decimal('100'), Decimal('9'), False),
        (Decimal('0.05'), Decimal('0.1'), Decimal('100'), Decimal('10'), False),
        (Decimal('0.05'), Decimal('0.1'), Decimal('100'), Decimal('11'), True),
        (Decimal('0.05'), Decimal('0.1'), Decimal('100'), Decimal('9'), False),
        (Decimal('0.05'), Decimal('0.1'), Decimal('200'), Decimal('10'), False),
        (Decimal('0.05'), Decimal('0.1'), Decimal('200'), Decimal('11'), False),
        (Decimal('0.05'), Decimal('0.1'), Decimal('200'), Decimal('9'), False),
        (Decimal('0.05'), Decimal('0.1'), Decimal('20'), Decimal('10'), True),
        (Decimal('0.05'), Decimal('0.1'), Decimal('20'), Decimal('11'), True),
        (Decimal('0.05'), Decimal('0.1'), Decimal('20'), Decimal('9'), True),
    ])
def test_check_within_limits(mocker, fcf_strategy, min_base_buy,
                             min_base_sell, buy_price, buy_quote_target,
                             expected_result):
    buy_trader = mocker.Mock()
    buy_trader.get_min_base_limit.return_value = min_base_buy
    buy_trader.quote_target_amount = buy_quote_target
    sell_trader = mocker.Mock()
    sell_trader.get_min_base_limit.return_value = min_base_sell
    fake_trade_metadata = TradeMetadata(
        spread_opp=None,
        buy_price=buy_price,
        sell_price=None,
        buy_trader=buy_trader,
        sell_trader=sell_trader
    )
    mocker.patch.object(fcf_strategy, 'trade_metadata',
                        fake_trade_metadata, create=True)

    result = fcf_strategy._FCFStrategy__check_within_limits()

    assert result == expected_result


@pytest.mark.parametrize('momentum_change', [True, False])
def test_evaluate_to_e1_trade(mocker, fcf_strategy, momentum_change):
    spread_opp = mocker.Mock()
    mocker.patch.object(fcf_strategy.state, 'e1_targets')
    mocker.patch.object(fcf_strategy, 'target_tracker')
    mocker.patch.object(fcf_strategy._manager, 'trader1')
    mocker.patch.object(fcf_strategy._manager, 'trader2')
    mocker.patch.object(fcf_strategy, '_FCFStrategy__prepare_trade')

    fcf_strategy._FCFStrategy__evaluate_to_e1_trade(
        momentum_change, spread_opp)

    fcf_strategy.target_tracker.advance_target_index.assert_called_with(
        spread_opp.e1_spread, fcf_strategy.state.e1_targets)
    fcf_strategy._FCFStrategy__prepare_trade.assert_called_with(
        momentum_change,
        fcf_strategy._manager.trader2,
        fcf_strategy._manager.trader1,
        fcf_strategy.state.e1_targets,
        spread_opp)


@pytest.mark.parametrize('momentum_change', [True, False])
def test_evaluate_to_e2_trade(mocker, fcf_strategy, momentum_change):
    spread_opp = mocker.Mock()
    mocker.patch.object(fcf_strategy.state, 'e2_targets')
    mocker.patch.object(fcf_strategy, 'target_tracker')
    mocker.patch.object(fcf_strategy._manager, 'trader1')
    mocker.patch.object(fcf_strategy._manager, 'trader2')
    mocker.patch.object(fcf_strategy, '_FCFStrategy__prepare_trade')

    fcf_strategy._FCFStrategy__evaluate_to_e2_trade(
        momentum_change, spread_opp)

    fcf_strategy.target_tracker.advance_target_index.assert_called_with(
        spread_opp.e2_spread, fcf_strategy.state.e2_targets)
    fcf_strategy._FCFStrategy__prepare_trade.assert_called_with(
        momentum_change,
        fcf_strategy._manager.trader1,
        fcf_strategy._manager.trader2,
        fcf_strategy.state.e2_targets,
        spread_opp)


@pytest.mark.parametrize('momentum, has_hit_targets', [
    (Momentum.NEUTRAL, [True]),
    (Momentum.NEUTRAL, [False, True]),
    (Momentum.NEUTRAL, [False, False, None]),
    (Momentum.TO_E1, [True]),
    (Momentum.TO_E1, [False, True]),
    (Momentum.TO_E1, [False, False, None]),
    (Momentum.TO_E2, [True]),
    (Momentum.TO_E2, [False, True]),
    (Momentum.TO_E2, [False, False, None]),
])
def test_is_trade_opportunity(mocker, fcf_strategy, momentum, has_hit_targets):
    # Setup fcf_strategy
    spread_opp = mocker.Mock()
    mocker.patch.object(fcf_strategy.state, 'momentum', momentum)
    mocker.patch.object(fcf_strategy.state, 'e1_targets')
    mocker.patch.object(fcf_strategy.state, 'e2_targets')
    mocker.patch.object(fcf_strategy, '_FCFStrategy__evaluate_to_e1_trade')
    mocker.patch.object(fcf_strategy, '_FCFStrategy__evaluate_to_e2_trade')
    mock_target_tracker = mocker.patch.object(fcf_strategy, 'target_tracker')
    mock_target_tracker.has_hit_targets.side_effect = has_hit_targets

    # Execute test
    result = fcf_strategy._FCFStrategy__is_trade_opportunity(
        spread_opp)

    # Check results
    if momentum is Momentum.NEUTRAL:
        if len(has_hit_targets) == 1:
            assert result is True
            assert fcf_strategy.state.momentum is Momentum.TO_E2
            fcf_strategy._FCFStrategy__evaluate_to_e2_trade \
                .assert_called_with(True, spread_opp)
            return
        if len(has_hit_targets) == 2:
            assert result is True
            assert fcf_strategy.state.momentum is Momentum.TO_E1
            fcf_strategy._FCFStrategy__evaluate_to_e1_trade \
                .assert_called_with(True, spread_opp)
            return
    if momentum is Momentum.TO_E1:
        if len(has_hit_targets) == 2:
            assert result is True
            assert fcf_strategy.state.momentum is Momentum.TO_E1
            fcf_strategy._FCFStrategy__evaluate_to_e1_trade \
                .assert_called_with(False, spread_opp)
            return
        if len(has_hit_targets) == 1:
            assert result is True
            assert fcf_strategy.state.momentum is Momentum.TO_E2
            fcf_strategy._FCFStrategy__evaluate_to_e2_trade \
                .assert_called_with(True, spread_opp)
            return
    if momentum is Momentum.TO_E2:
        if len(has_hit_targets) == 2:
            assert result is True
            assert fcf_strategy.state.momentum is Momentum.TO_E1
            fcf_strategy._FCFStrategy__evaluate_to_e1_trade \
                .assert_called_with(True, spread_opp)
            return
        if len(has_hit_targets) == 1:
            assert result is True
            assert fcf_strategy.state.momentum is Momentum.TO_E2
            fcf_strategy._FCFStrategy__evaluate_to_e2_trade \
                .assert_called_with(False, spread_opp)
            return

    assert result is False


@pytest.mark.parametrize('is_momentum_change', [True, False])
@pytest.mark.parametrize('chunks_complete', [True, False])
@pytest.mark.parametrize('to_e1', [True, False])
@pytest.mark.parametrize(
    'next_quote_vol, buy_quote_balance, buy_price, sell_base_balance, '
    'result_quote_target_amount', [
        (Decimal('2001'), Decimal('2000'), Decimal('1000'), Decimal('2'), Decimal('2000')),
        (Decimal('2000'), Decimal('2001'), Decimal('1000'), Decimal('2'), Decimal('2000')),
        (Decimal('2001'), Decimal('2000'), Decimal('1000'), Decimal('1.9'), None),
        (Decimal('2000'), Decimal('2001'), Decimal('1000'), Decimal('1.9'), None),
    ])
def test_prepare_trade(mocker, fcf_strategy, is_momentum_change,
                       chunks_complete, to_e1, next_quote_vol,
                       buy_quote_balance, buy_price, sell_base_balance,
                       result_quote_target_amount):
    # Chosen for the roughly round numbers.
    targets = [(x, 1000 + 200*x) for x in range(1, 10, 2)]
    spread_opp = mocker.Mock()
    spread_opp.e1_buy, spread_opp.e2_buy = buy_price, buy_price
    mock_tracker = mocker.patch.object(fcf_strategy, 'target_tracker')
    mock_tracker.trade_completed = chunks_complete
    mock_chunker = mocker.patch.object(fcf_strategy, 'trade_chunker')
    mocker.patch.object(
        fcf_strategy._manager,
        'trader1',
        CCXTTrader('ETH', 'USD', 'kraken', Decimal('0')))
    mocker.patch.object(
        fcf_strategy._manager,
        'trader2',
        CCXTTrader('ETH', 'USD', 'bitfinex', Decimal('0')))

    if to_e1:
        buy_trader = fcf_strategy._manager.trader2
        sell_trader = fcf_strategy._manager.trader1
    else:
        buy_trader = fcf_strategy._manager.trader1
        sell_trader = fcf_strategy._manager.trader2

    mock_get_quote_from_usd = mocker.patch.object(
        buy_trader, 'get_quote_from_usd', return_value=next_quote_vol)

    buy_trader.quote_bal = buy_quote_balance
    sell_trader.base_bal = sell_base_balance

    if result_quote_target_amount is None:
        with pytest.raises(InsufficientCryptoBalance):
            fcf_strategy._FCFStrategy__prepare_trade(
                is_momentum_change, buy_trader, sell_trader, targets,
                spread_opp)
    else:
        fcf_strategy._FCFStrategy__prepare_trade(
            is_momentum_change, buy_trader, sell_trader, targets, spread_opp)

    sell_price_result = fcf_strategy.trade_metadata.sell_price
    if to_e1:
        assert sell_price_result == spread_opp.e1_sell
    else:
        assert sell_price_result == spread_opp.e2_sell
    mock_chunker.get_next_trade.assert_called_once_with()
    mock_get_quote_from_usd.assert_called_once_with(
        mock_chunker.get_next_trade.return_value)




@pytest.mark.parametrize('is_trader1_buy', [True, False])
def test_update_trade_targets(mocker, fcf_strategy, is_trader1_buy):
    mock_targets = ['list', 'of', 'targets']
    mock_spread_opp = mocker.Mock()
    mocker.patch.object(
        fcf_strategy, '_FCFStrategy__calc_targets', return_value=mock_targets)
    if is_trader1_buy:
        mocker.patch.object(fcf_strategy, 'trade_metadata', TradeMetadata(
            spread_opp=mock_spread_opp,
            buy_price=None,
            sell_price=None,
            buy_trader=fcf_strategy._manager.trader1,
            sell_trader=fcf_strategy._manager.trader2
        ), create=True)
    else:
        mocker.patch.object(fcf_strategy, 'trade_metadata', TradeMetadata(
            spread_opp=mock_spread_opp,
            buy_price=None,
            sell_price=None,
            buy_trader=fcf_strategy._manager.trader2,
            sell_trader=fcf_strategy._manager.trader1
        ), create=True)
    mocker.patch.object(fcf_strategy.state, 'h_to_e1_max')
    mocker.patch.object(fcf_strategy.state, 'h_to_e2_max')
    mocker.patch.object(fcf_strategy._manager.trader1, 'get_usd_balance')
    mocker.patch.object(fcf_strategy._manager.trader2, 'get_usd_balance')

    fcf_strategy._FCFStrategy__update_trade_targets()

    if is_trader1_buy:
        fcf_strategy._FCFStrategy__calc_targets.assert_called_with(
            mock_spread_opp.e1_spread,
            fcf_strategy.state.h_to_e1_max,
            fcf_strategy._manager.trader2.get_usd_balance())
        assert fcf_strategy.state.e1_targets == mock_targets
    else:
        fcf_strategy._FCFStrategy__calc_targets.assert_called_with(
            mock_spread_opp.e2_spread,
            fcf_strategy.state.h_to_e2_max,
            fcf_strategy._manager.trader1.get_usd_balance())
        assert fcf_strategy.state.e2_targets == mock_targets


def test_clean_up(fcf_strategy):
    fcf_strategy.clean_up()
    assert fcf_strategy.trade_metadata == None


@pytest.mark.parametrize('chunks_complete', [True, False])
def test_finalize_trade(mocker, fcf_strategy, chunks_complete):
    mock_buy_response = {'post_fee_quote': 'fake data'}
    mock_sell_response = mocker.Mock()
    mock_post_fee_usd = mocker.Mock()
    mock_min_usd_trade_size = mocker.Mock()
    mock_chunker = mocker.patch.object(fcf_strategy, 'trade_chunker')
    mock_chunker.trade_completed = chunks_complete
    mock_tracker = mocker.patch.object(fcf_strategy, 'target_tracker')
    mock_metadata = mocker.patch.object(
        fcf_strategy, 'trade_metadata', create=True)
    mock_metadata.buy_trader.get_usd_from_quote.side_effect = [
        mock_post_fee_usd, mock_min_usd_trade_size
    ]
    mock_trader1 = mocker.patch.object(fcf_strategy._manager, 'trader1')
    mock_trader2 = mocker.patch.object(fcf_strategy._manager, 'trader2')
    mock_update_targets = mocker.patch.object(
        fcf_strategy, '_FCFStrategy__update_trade_targets')
    mock_update_targets = mocker.patch.object(
        fcf_strategy, '_FCFStrategy__get_min_target_amount')

    fcf_strategy.finalize_trade(mock_buy_response, mock_sell_response)

    assert mock_metadata.buy_trader.get_usd_from_quote.call_count == 2
    mock_chunker.finalize_trade.assert_called_once_with(
        mock_post_fee_usd, mock_min_usd_trade_size)
    mock_trader1.update_wallet_balances.assert_called_once_with()
    mock_trader2.update_wallet_balances.assert_called_once_with()
    mock_update_targets.assert_called_once_with()

    if chunks_complete:
        mock_tracker.increment.assert_called_once_with()


def test_get_trade_data(mocker, fcf_strategy):
    mock_trade_data = mocker.Mock()
    mocker.patch.object(fcf_strategy, 'trade_metadata', mock_trade_data, create=True)
    result = fcf_strategy.get_trade_data()
    assert result is mock_trade_data


@pytest.mark.parametrize('vol_min', [Decimal('100'), Decimal('1000')])
@pytest.mark.parametrize('e1_quote_balance', [Decimal('0'), Decimal('2000')])
@pytest.mark.parametrize('e2_quote_balance', [Decimal('0'), Decimal('2000')])
@pytest.mark.parametrize('exc_type', [None, NetworkError, OrderbookException])
@pytest.mark.parametrize('has_started', [True, False])
@pytest.mark.parametrize('e1_spread', [Decimal('5'), Decimal('50')])
@pytest.mark.parametrize('e2_spread', [Decimal('0'), Decimal('3')])
@pytest.mark.parametrize('h_to_e1_max', [Decimal('5'), Decimal('50')])
@pytest.mark.parametrize('h_to_e2_max', [Decimal('0'), Decimal('3')])
@pytest.mark.parametrize('is_opportunity', [True, False])
@pytest.mark.parametrize('is_in_limits', [True, False])
def test_poll_opportunity(mocker, fcf_strategy, vol_min, e1_quote_balance,
                          e2_quote_balance, exc_type,
                          has_started, e1_spread, e2_spread, h_to_e1_max,
                          h_to_e2_max, is_opportunity, is_in_limits):
    trader1 = mocker.Mock()
    trader2 = mocker.Mock()
    balance_checker = mocker.Mock()
    mocker.patch.object(
        fcf_strategy._manager, 'balance_checker', balance_checker)
    mocker.patch.object(
        fcf_strategy._manager, 'checkpoint')
    mocker.patch.object(
        fcf_strategy._manager.checkpoint, 'strategy_state')
    mocker.patch.object(
        fcf_strategy._manager, 'trader1', trader1)
    mocker.patch.object(
        fcf_strategy._manager, 'trader2', trader2)
    mocker.patch.object(
        fcf_strategy._manager.trader1, 'get_usd_balance', return_value=e1_quote_balance)
    mocker.patch.object(
        fcf_strategy._manager.trader2, 'get_usd_balance', return_value=e2_quote_balance)
    mocker.patch.object(
        fcf_strategy._manager.trader1, 'set_target_amounts')
    mocker.patch.object(
        fcf_strategy._manager.trader2, 'set_target_amounts')
    mocker.patch.object(
        fcf_strategy, '_vol_min', vol_min)
    mocker.patch.object(fcf_strategy.state, 'has_started', has_started)
    mocker.patch.object(fcf_strategy.state, 'h_to_e1_max', h_to_e1_max)
    mocker.patch.object(fcf_strategy.state, 'h_to_e2_max', h_to_e2_max)
    spread_opp = mocker.Mock()
    spread_opp.e1_spread = e1_spread
    spread_opp.e2_spread = e2_spread
    calc_targets = mocker.patch.object(fcf_strategy,
                                       '_FCFStrategy__calc_targets')
    is_trade_opportunity = mocker.patch.object(fcf_strategy,
                                               '_FCFStrategy__is_trade_opportunity',
                                               return_value=is_opportunity)
    is_within_limits = mocker.patch.object(fcf_strategy,
                                           '_FCFStrategy__check_within_limits',
                                           return_value=is_in_limits)
    update_targets = mocker.patch.object(fcf_strategy,
                                         '_FCFStrategy__update_trade_targets')
    mocker.patch.object(
        arbseeker, 'get_spreads_by_ob', return_value=spread_opp)
    if exc_type:
        arbseeker.get_spreads_by_ob.side_effect = exc_type

    is_opportunity_result = fcf_strategy.poll_opportunity()

    fcf_strategy._manager.trader1.set_target_amounts.assert_called_once_with(
        max(vol_min, e1_quote_balance))
    fcf_strategy._manager.trader2.set_target_amounts.assert_called_once_with(
        max(vol_min, e2_quote_balance))

    if exc_type:
        assert is_opportunity_result is False
        calc_targets.assert_not_called()
        is_trade_opportunity.assert_not_called()
    else:
        if not has_started:
            assert fcf_strategy.state.momentum == Momentum.NEUTRAL
            assert isinstance(fcf_strategy.target_tracker, FCFTargetTracker)
            assert isinstance(fcf_strategy.trade_chunker, FCFTradeChunker)
            assert fcf_strategy.has_started is True
            assert calc_targets.call_count == 2
            assert is_opportunity_result is False
            is_trade_opportunity.assert_not_called()
        else:
            is_trade_opportunity.assert_called_with(spread_opp)
            calc_targets.assert_not_called()
            if is_opportunity:
                is_within_limits.assert_called_once_with()
                if not is_within_limits:
                    update_targets.assert_called_once_with()
            else:
                is_within_limits.assert_not_called()
            assert is_opportunity_result == (is_opportunity and is_in_limits)
        assert fcf_strategy.state.h_to_e1_max == max(
            h_to_e1_max, e1_spread)
        assert fcf_strategy.state.h_to_e2_max == max(
            h_to_e2_max, e2_spread)
        balance_checker.check_crypto_balances.assert_called_with(spread_opp)
