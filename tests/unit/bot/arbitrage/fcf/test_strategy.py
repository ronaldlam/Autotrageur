import uuid
from decimal import Decimal

import pytest
from ccxt import NetworkError

import bot.arbitrage.arbseeker as arbseeker
from bot.arbitrage.arbseeker import SpreadOpportunity
from bot.arbitrage.fcf.strategy import FCFStrategy, InsufficientCryptoBalance
from bot.common.enums import Momentum
from bot.trader.ccxt_trader import CCXTTrader, OrderbookException

FAKE_CONFIG_UUID = str(uuid.uuid4())


@pytest.fixture(scope='module')
def fcf_strategy():
    return FCFStrategy(None, None, None, None, None, None, None,
        CCXTTrader('ETH', 'USD', 'kraken', Decimal('0')),
        CCXTTrader('ETH', 'USD', 'bitfinex', Decimal('0')))


@pytest.mark.parametrize('spread, start, result', [
    (-1, 0, 0),
    (3, 0, 2),
    (5, 0, 3),
    (3, 1, 2),
    (5, 2, 3),
    (9, 2, 5),
    (-1, 2, 2),
    (1, 2, 2),
    (3, 2, 2),
])
def test_advance_target_index(
        mocker, fcf_strategy, spread, start, result):
    # Chosen for the roughly round numbers.
    targets = [(x, 1000 + 200*x) for x in range(-1, 10, 2)]
    mocker.patch.object(
        fcf_strategy, 'target_index', start, create=True)
    fcf_strategy._FCFStrategy__advance_target_index(
        spread, targets)
    assert fcf_strategy.target_index == result


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
        fcf_strategy, 'spread_min', Decimal('1'), create=True)
    mocker.patch.object(
        fcf_strategy, 'vol_min', vol_min, create=True)
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
    fake_trade_metadata = {
        'buy_trader': buy_trader,
        'sell_trader': sell_trader,
        'buy_price': buy_price
    }
    mocker.patch.object(fcf_strategy, 'trade_metadata',
                        fake_trade_metadata, create=True)

    result = fcf_strategy._FCFStrategy__check_within_limits()

    assert result == expected_result


@pytest.mark.parametrize('momentum_change', [True, False])
def test_evaluate_to_e1_trade(mocker, fcf_strategy, momentum_change):
    spread_opp = mocker.Mock()
    mocker.patch.object(fcf_strategy, 'e1_targets', create=True)
    mocker.patch.object(fcf_strategy, 'h_to_e2_max')
    mocker.patch.object(fcf_strategy, 'trader1')
    mocker.patch.object(fcf_strategy, 'trader2')
    mocker.patch.object(
        fcf_strategy, '_FCFStrategy__advance_target_index')
    mocker.patch.object(fcf_strategy, '_FCFStrategy__prepare_trade')

    fcf_strategy._FCFStrategy__evaluate_to_e1_trade(
        momentum_change, spread_opp)

    fcf_strategy._FCFStrategy__advance_target_index.assert_called_with(
        spread_opp.e1_spread, fcf_strategy.e1_targets)
    fcf_strategy._FCFStrategy__prepare_trade.assert_called_with(
        momentum_change, fcf_strategy.trader2, fcf_strategy.trader1,
        fcf_strategy.e1_targets, spread_opp)


@pytest.mark.parametrize('momentum_change', [True, False])
def test_evaluate_to_e2_trade(mocker, fcf_strategy, momentum_change):
    spread_opp = mocker.Mock()
    mocker.patch.object(fcf_strategy, 'e2_targets', create=True)
    mocker.patch.object(fcf_strategy, 'h_to_e1_max')
    mocker.patch.object(fcf_strategy, 'trader1')
    mocker.patch.object(fcf_strategy, 'trader2')
    mocker.patch.object(
        fcf_strategy, '_FCFStrategy__advance_target_index')
    mocker.patch.object(fcf_strategy, '_FCFStrategy__prepare_trade')

    fcf_strategy._FCFStrategy__evaluate_to_e2_trade(
        momentum_change, spread_opp)

    fcf_strategy._FCFStrategy__advance_target_index.assert_called_with(
        spread_opp.e2_spread, fcf_strategy.e2_targets)
    fcf_strategy._FCFStrategy__prepare_trade.assert_called_with(
        momentum_change, fcf_strategy.trader1, fcf_strategy.trader2,
        fcf_strategy.e2_targets, spread_opp)


@pytest.mark.parametrize('e1_spread, e2_spread, momentum, target_index', [
    (Decimal('-3'), Decimal('3'), Momentum.NEUTRAL, 1),
    (Decimal('3'), Decimal('-3'), Momentum.NEUTRAL, 1),
    (Decimal('-3'), Decimal('3'), Momentum.TO_E1, 1),
    (Decimal('3'), Decimal('-3'), Momentum.TO_E1, 1),
    (Decimal('-3'), Decimal('3'), Momentum.TO_E2, 1),
    (Decimal('3'), Decimal('-3'), Momentum.TO_E2, 1),
    (Decimal('-2'), Decimal('0'), Momentum.NEUTRAL, 1),
    (Decimal('-2'), Decimal('0'), Momentum.TO_E1, 1),
    (Decimal('-2'), Decimal('0'), Momentum.TO_E2, 1),
    (None, Decimal('-3'), Momentum.NEUTRAL, 1),
    (Decimal('-3'), None, Momentum.NEUTRAL, 1),
])
def test_is_trade_opportunity(
        mocker, fcf_strategy, e1_spread, e2_spread, momentum, target_index):
    # Setup fcf_strategy
    spread_opp = SpreadOpportunity(
        FAKE_CONFIG_UUID, e1_spread, e2_spread, None, None, None, None, None, None)
    mocker.patch.object(fcf_strategy, 'momentum', momentum, create=True)
    mocker.patch.object(fcf_strategy, 'target_index',
                        target_index, create=True)
    # Chosen for the roughly round numbers.
    e1_targets = [(Decimal(x), Decimal(1000 + 200*x)) for x in range(-1, 4, 2)]
    e2_targets = [(Decimal(x), Decimal(1000 + 200*x)) for x in range(1, 10, 2)]
    mocker.patch.object(fcf_strategy, 'e1_targets', e1_targets, create=True)
    mocker.patch.object(fcf_strategy, 'e2_targets', e2_targets, create=True)
    mocker.patch.object(
        fcf_strategy, '_FCFStrategy__evaluate_to_e1_trade')
    mocker.patch.object(
        fcf_strategy, '_FCFStrategy__evaluate_to_e2_trade')

    # Execute test
    if e1_spread is None or e2_spread is None:
        with pytest.raises(TypeError):
            fcf_strategy._FCFStrategy__is_trade_opportunity(spread_opp)
        return
    else:
        result = fcf_strategy._FCFStrategy__is_trade_opportunity(
            spread_opp)

    # Check results
    if momentum is Momentum.NEUTRAL:
        if e2_spread >= fcf_strategy.e2_targets[target_index][0]:
            assert result is True
            assert fcf_strategy.momentum is Momentum.TO_E2
            fcf_strategy._FCFStrategy__evaluate_to_e2_trade \
                .assert_called_with(True, spread_opp)
            return
        if e1_spread >= fcf_strategy.e1_targets[target_index][0]:
            assert result is True
            assert fcf_strategy.momentum is Momentum.TO_E1
            fcf_strategy._FCFStrategy__evaluate_to_e1_trade \
                .assert_called_with(True, spread_opp)
            return
    if momentum is Momentum.TO_E1:
        if e1_spread >= fcf_strategy.e1_targets[target_index][0]:
            assert result is True
            assert fcf_strategy.momentum is Momentum.TO_E1
            fcf_strategy._FCFStrategy__evaluate_to_e1_trade \
                .assert_called_with(False, spread_opp)
            return
        if e2_spread >= fcf_strategy.e2_targets[target_index][0]:
            assert result is True
            assert fcf_strategy.momentum is Momentum.TO_E2
            fcf_strategy._FCFStrategy__evaluate_to_e2_trade \
                .assert_called_with(True, spread_opp)
            return
    if momentum is Momentum.TO_E2:
        if e1_spread >= fcf_strategy.e1_targets[target_index][0]:
            assert result is True
            assert fcf_strategy.momentum is Momentum.TO_E1
            fcf_strategy._FCFStrategy__evaluate_to_e1_trade \
                .assert_called_with(True, spread_opp)
            return
        if e2_spread >= fcf_strategy.e2_targets[target_index][0]:
            assert result is True
            assert fcf_strategy.momentum is Momentum.TO_E2
            fcf_strategy._FCFStrategy__evaluate_to_e2_trade \
                .assert_called_with(False, spread_opp)
            return

    assert result is False


@pytest.mark.parametrize(
    'is_momentum_change, to_e1, target_index, last_target_index, '
    'buy_quote_balance, buy_price, sell_base_balance, result', [
        (True, True, 0, 0, Decimal('2000'), Decimal('1000'), Decimal('2'),
            {'target_index': 1, 'last_target_index': 0, 'quote_target_amount': Decimal('1200')}),
        (True, False, 0, 0, Decimal('2000'), Decimal('1000'), Decimal('2'),
            {'target_index': 1, 'last_target_index': 0, 'quote_target_amount': Decimal('1200')}),
        (False, True, 2, 0, Decimal('2000'), Decimal('1000'), Decimal('2'),
            {'target_index': 3, 'last_target_index': 2, 'quote_target_amount': Decimal('800')}),
        (False, False, 2, 0, Decimal('2000'), Decimal('1000'), Decimal('2'),
            {'target_index': 3, 'last_target_index': 2, 'quote_target_amount': Decimal('800')}),
        (True, True, 0, 0, Decimal('600'), Decimal('1000'), Decimal('2'),
            {'target_index': 1, 'last_target_index': 0, 'quote_target_amount': Decimal('600')}),
        (True, False, 0, 0, Decimal('600'), Decimal('1000'), Decimal('2'),
            {'target_index': 1, 'last_target_index': 0, 'quote_target_amount': Decimal('600')}),
        (False, True, 2, 0, Decimal('600'), Decimal('1000'), Decimal('2'),
            {'target_index': 3, 'last_target_index': 2, 'quote_target_amount': Decimal('600')}),
        (False, False, 2, 0, Decimal('600'), Decimal('1000'), Decimal('2'),
            {'target_index': 3, 'last_target_index': 2, 'quote_target_amount': Decimal('600')}),
        (True, True, 0, 0, Decimal('2000'), Decimal('1000'), Decimal('0.5'), None),
        (True, False, 0, 0, Decimal('2000'), Decimal('1000'), Decimal('0.5'), None),
        (False, True, 2, 0, Decimal('2000'), Decimal('1000'), Decimal('0.5'), None),
        (False, False, 2, 0, Decimal('2000'),
         Decimal('1000'), Decimal('0.5'), None),
        (True, True, 0, 0, Decimal('600'), Decimal('1000'), Decimal('0.5'), None),
        (True, False, 0, 0, Decimal('600'), Decimal('1000'), Decimal('0.5'), None),
        (False, True, 2, 0, Decimal('600'), Decimal('1000'), Decimal('0.5'), None),
        (False, False, 2, 0, Decimal('600'), Decimal('1000'), Decimal('0.5'), None),
    ])
def test_prepare_trade(mocker, fcf_strategy, is_momentum_change, to_e1,
                       target_index, last_target_index, buy_quote_balance,
                       buy_price, sell_base_balance, result):
    # Chosen for the roughly round numbers.
    targets = [(x, 1000 + 200*x) for x in range(1, 10, 2)]
    spread_opp = mocker.Mock()
    spread_opp.e1_buy, spread_opp.e2_buy = buy_price, buy_price
    mocker.patch.object(
        fcf_strategy, 'target_index', target_index, create=True)
    mocker.patch.object(
        fcf_strategy, 'last_target_index', last_target_index, create=True)

    if to_e1:
        buy_trader = fcf_strategy.trader2
        sell_trader = fcf_strategy.trader1
    else:
        buy_trader = fcf_strategy.trader1
        sell_trader = fcf_strategy.trader2

    buy_trader.quote_bal = buy_quote_balance
    sell_trader.base_bal = sell_base_balance

    if result is None:
        with pytest.raises(InsufficientCryptoBalance):
            fcf_strategy._FCFStrategy__prepare_trade(
                is_momentum_change, buy_trader, sell_trader, targets,
                spread_opp)
        return

    fcf_strategy._FCFStrategy__prepare_trade(
        is_momentum_change, buy_trader, sell_trader, targets, spread_opp)

    sell_price_result = fcf_strategy.trade_metadata['sell_price']
    if to_e1:
        assert sell_price_result == spread_opp.e1_sell
    else:
        assert sell_price_result == spread_opp.e2_sell
    assert fcf_strategy.target_index == result['target_index']
    assert fcf_strategy.last_target_index == result['last_target_index']
    assert buy_trader.quote_target_amount == result['quote_target_amount']


@pytest.mark.parametrize('is_trader1_buy', [True, False])
def test_update_trade_targets(mocker, fcf_strategy, is_trader1_buy):
    mock_targets = ['list', 'of', 'targets']
    mock_spread_opp = mocker.Mock()
    mocker.patch.object(
        fcf_strategy, '_FCFStrategy__calc_targets', return_value=mock_targets)
    if is_trader1_buy:
        mocker.patch.object(fcf_strategy, 'trade_metadata', {
            'spread_opp': mock_spread_opp,
            'buy_trader': fcf_strategy.trader1,
            'sell_trader': fcf_strategy.trader2
        }, create=True)
    else:
        mocker.patch.object(fcf_strategy, 'trade_metadata', {
            'spread_opp': mock_spread_opp,
            'buy_trader': fcf_strategy.trader2,
            'sell_trader': fcf_strategy.trader1
        }, create=True)
    mocker.patch.object(fcf_strategy, 'h_to_e1_max', create=True)
    mocker.patch.object(fcf_strategy, 'h_to_e2_max', create=True)
    mocker.patch.object(fcf_strategy.trader1, 'get_usd_balance')
    mocker.patch.object(fcf_strategy.trader2, 'get_usd_balance')

    fcf_strategy._FCFStrategy__update_trade_targets()

    if is_trader1_buy:
        fcf_strategy._FCFStrategy__calc_targets.assert_called_with(
            mock_spread_opp.e1_spread,
            fcf_strategy.h_to_e1_max,
            fcf_strategy.trader2.get_usd_balance())
        assert fcf_strategy.e1_targets == mock_targets
    else:
        fcf_strategy._FCFStrategy__calc_targets.assert_called_with(
            mock_spread_opp.e2_spread,
            fcf_strategy.h_to_e2_max,
            fcf_strategy.trader1.get_usd_balance())
        assert fcf_strategy.e2_targets == mock_targets


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
        fcf_strategy, 'balance_checker', balance_checker, create=True)
    mocker.patch.object(
        fcf_strategy, 'checkpoint', create=True)
    mocker.patch.object(fcf_strategy.checkpoint, 'save')
    mocker.patch.object(
        fcf_strategy, 'trader1', trader1, create=True)
    mocker.patch.object(
        fcf_strategy, 'trader2', trader2, create=True)
    mocker.patch.object(
        fcf_strategy.trader1, 'get_usd_balance', return_value=e1_quote_balance)
    mocker.patch.object(
        fcf_strategy.trader2, 'get_usd_balance', return_value=e2_quote_balance)
    mocker.patch.object(
        fcf_strategy.trader1, 'set_target_amounts')
    mocker.patch.object(
        fcf_strategy.trader2, 'set_target_amounts')
    mocker.patch.object(
        fcf_strategy, 'vol_min', vol_min, create=True)
    mocker.patch.object(
        fcf_strategy, 'has_started', has_started, create=True)
    mocker.patch.object(
        fcf_strategy, 'h_to_e1_max', h_to_e1_max, create=True)
    mocker.patch.object(
        fcf_strategy, 'h_to_e2_max', h_to_e2_max, create=True)
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

    fcf_strategy.trader1.set_target_amounts.assert_called_once_with(
        max(vol_min, e1_quote_balance))
    fcf_strategy.trader2.set_target_amounts.assert_called_once_with(
        max(vol_min, e2_quote_balance))

    if exc_type:
        assert is_opportunity_result is False
        calc_targets.assert_not_called()
        is_trade_opportunity.assert_not_called()
    else:
        if not has_started:
            assert fcf_strategy.momentum == Momentum.NEUTRAL
            assert fcf_strategy.target_index == 0
            assert fcf_strategy.last_target_index == 0
            assert fcf_strategy.has_started is True
            assert calc_targets.call_count == 2
            assert is_opportunity_result is False
            is_trade_opportunity.assert_not_called()
        else:
            fcf_strategy.checkpoint.save.assert_called_once_with(
                fcf_strategy)
            is_trade_opportunity.assert_called_with(spread_opp)
            calc_targets.assert_not_called()
            if is_opportunity:
                is_within_limits.assert_called_once_with()
                if not is_within_limits:
                    update_targets.assert_called_once_with()
            else:
                is_within_limits.assert_not_called()
            assert is_opportunity_result == (is_opportunity and is_in_limits)
        assert fcf_strategy.h_to_e1_max == max(
            h_to_e1_max, e1_spread)
        assert fcf_strategy.h_to_e2_max == max(
            h_to_e2_max, e2_spread)
        balance_checker.check_crypto_balances.assert_called_with(spread_opp)
