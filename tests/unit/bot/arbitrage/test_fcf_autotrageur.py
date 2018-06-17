import copy
from decimal import Decimal, InvalidOperation

import pytest
from ccxt import NetworkError

import bot.arbitrage.arbseeker as arbseeker
import bot.arbitrage.fcf_autotrageur
import libs.email_client.simple_email_client
from bot.arbitrage.arbseeker import SpreadOpportunity
from bot.arbitrage.fcf_autotrageur import (EMAIL_HIGH_SPREAD_HEADER,
                                           EMAIL_LOW_SPREAD_HEADER,
                                           EMAIL_NONE_SPREAD, FCFAutotrageur,
                                           InsufficientCryptoBalance,
                                           arbseeker, email_count, prev_spread)
from bot.common.config_constants import (DRYRUN, H_TO_E1_MAX, H_TO_E2_MAX,
                                         SPREAD_MIN, VOL_MIN)
from bot.common.enums import Momentum

xfail = pytest.mark.xfail


@pytest.fixture(scope='module')
def no_patch_fcf_autotrageur():
    return FCFAutotrageur()


@pytest.fixture()
def fcf_autotrageur(mocker, fake_ccxt_trader):
    f = FCFAutotrageur()
    f.config = {
        'email_cfg_path': 'fake/path/to/config.yaml',
        'spread_target_low': 1.0,
        'spread_target_high': 5.0
    }
    trader1 = fake_ccxt_trader
    trader2 = copy.deepcopy(fake_ccxt_trader)
    mocker.patch.object(f, 'trader1', trader1, create=True)
    mocker.patch.object(f, 'trader2', trader2, create=True)
    f.message = 'fake message'
    # f.spread_opp = { arbseeker.SPREAD: 1.0 }
    return f

class TestIsWithinTolerance:
    @pytest.mark.parametrize('curr_spread, prev_spread, spread_rnd, spread_tol, bTol', [
        (Decimal('0'), Decimal('0'), 0, Decimal('0'), True),
        (Decimal('0'), Decimal('0'), None, Decimal('0'), True),
        (Decimal('0'), Decimal('0'), 0, Decimal('1'), True),
        (Decimal('0'), Decimal('0'), None, Decimal('1'), True),
        (Decimal('0.0'), Decimal('1.0'), 1, Decimal('1.0'), True),
        (Decimal('0.0'), Decimal('1.0'), None, Decimal('1.0'), True),
        (Decimal('1.0'), Decimal('0.0'), 1, Decimal('1.0'), True),
        (Decimal('1.0'), Decimal('0.0'), None, Decimal('1.0'), True),
        (Decimal('0.0'), Decimal('1.1'), 1, Decimal('1.0'), False),
        (Decimal('0.0'), Decimal('1.1'), None, Decimal('1.0'), False),
        (Decimal('100.001'), Decimal('100.002'), None, Decimal('0.001'), True),
        (Decimal('100.001'), Decimal('100.002'), 0, Decimal('0.001'), True),
        (Decimal('100.001'), Decimal('100.002'), 20, Decimal('0.001'), True),
        (Decimal('100.001'), Decimal('100.002'), None, Decimal('0.0001'), False),
        (Decimal('1000000.12345678'), Decimal('1000000.12345679'), None, Decimal('0.00000001'), True),
        (Decimal('1000000.12345678'), Decimal('1000000.12345679'), 1, Decimal('0.00000001'), True),
        (Decimal('1000000.12345678'), Decimal('1000000.12345679'), None, Decimal('0.000000001'), False)
    ])
    def test_is_within_tolerance(
            self, curr_spread, prev_spread, spread_rnd, spread_tol, bTol):
        in_tolerance = FCFAutotrageur._is_within_tolerance(
            curr_spread, prev_spread, spread_rnd, spread_tol)
        assert in_tolerance is bTol

    @pytest.mark.parametrize('curr_spread, prev_spread, spread_rnd, spread_tol, bTol', [
        (None, None, None, None, True),
        (None, Decimal('1'), 1, Decimal('0.1'), True),
        (Decimal('1'), None, 1, Decimal('0.1'), True),
        (Decimal('1'), Decimal('1'), 1, None, True)
    ])
    def test_is_within_tolerance_bad(
            self, curr_spread, prev_spread, spread_rnd, spread_tol, bTol):
        with pytest.raises((InvalidOperation, TypeError), message="Expecting a Decimal or int, not a NoneType"):
            in_tolerance = FCFAutotrageur._is_within_tolerance(
                curr_spread, prev_spread, spread_rnd, spread_tol)
            assert in_tolerance is bTol


TARGETS = [(x, 1000 + 200*x) for x in range(-1, 10, 2)]


@pytest.mark.parametrize('spread, targets, start, result', [
    (-1, TARGETS, 0, 0),
    (3, TARGETS, 0, 2),
    (5, TARGETS, 0, 3),
    (3, TARGETS, 1, 2),
    (5, TARGETS, 2, 3),
    (9, TARGETS, 2, 5),
    (-1, TARGETS, 2, 2),
    (1, TARGETS, 2, 2),
    (3, TARGETS, 2, 2),
])
def test_advance_target_index(
        fcf_autotrageur, spread, targets, start, result):
    fcf_autotrageur.target_index = start
    fcf_autotrageur._FCFAutotrageur__advance_target_index(spread, targets)
    assert fcf_autotrageur.target_index == result


@pytest.mark.parametrize(
    'vol_min, spread, h_max, from_balance, result', [
        (Decimal('1000'), Decimal('4'), Decimal('2'), Decimal('1000'), [(Decimal('5'), Decimal('1000'))]), # spread > h_max
        (Decimal('2000'), Decimal('2'), Decimal('3'), Decimal('1000'), [(Decimal('3'), Decimal('1000'))]), # spread < h_max
        (Decimal('1000'), Decimal('2'), Decimal('3'), Decimal('2000'), [(Decimal('3'), Decimal('2000'))]),
        (Decimal('1000'), Decimal('2'), Decimal('4'), Decimal('2000'), [(Decimal('3'), Decimal('1000')), (Decimal('4'), Decimal('2000'))]),
        (Decimal('500'), Decimal('2'), Decimal('5'), Decimal('2000'), [(Decimal('3'), Decimal('500')), (Decimal('4'), Decimal('1000')), (Decimal('5'), Decimal('2000'))]),
        (Decimal('2000'), Decimal('2'), Decimal('5'), Decimal('2000'), [(Decimal('3'), Decimal('2000')), (Decimal('4'), Decimal('2000')), (Decimal('5'), Decimal('2000'))])
])
def test_calc_targets(fcf_autotrageur, vol_min, spread, h_max, from_balance, result):
    fcf_autotrageur.spread_min = Decimal('1')
    fcf_autotrageur.vol_min = vol_min
    targets = fcf_autotrageur._FCFAutotrageur__calc_targets(
        spread, h_max, from_balance)
    assert targets == result


@pytest.mark.parametrize('momentum_change', [(True), (False)])
def test_evaluate_to_e1_trade(mocker, fcf_autotrageur, momentum_change):
    spread_opp = mocker.Mock()
    fcf_autotrageur.e1_targets = mocker.Mock()
    fcf_autotrageur.h_to_e2_max = mocker.Mock()
    fcf_autotrageur.trader1 = mocker.Mock()
    fcf_autotrageur.trader2 = mocker.Mock()
    mocker.patch.object(
        fcf_autotrageur, '_FCFAutotrageur__advance_target_index')
    mocker.patch.object(fcf_autotrageur, '_FCFAutotrageur__prepare_trade')
    mock_targets = mocker.Mock()
    mocker.patch.object(fcf_autotrageur, '_FCFAutotrageur__calc_targets', return_value=mock_targets)

    fcf_autotrageur._FCFAutotrageur__evaluate_to_e1_trade(
        momentum_change, spread_opp)

    fcf_autotrageur._FCFAutotrageur__advance_target_index.assert_called_with(
        spread_opp.e1_spread, fcf_autotrageur.e1_targets)
    fcf_autotrageur._FCFAutotrageur__prepare_trade.assert_called_with(
        momentum_change, fcf_autotrageur.trader2, fcf_autotrageur.trader1,
        fcf_autotrageur.e1_targets, spread_opp)
    fcf_autotrageur._FCFAutotrageur__calc_targets.assert_called_with(
        spread_opp.e2_spread, fcf_autotrageur.h_to_e2_max,
        fcf_autotrageur.trader1.quote_bal)
    assert fcf_autotrageur.e2_targets == mock_targets


@pytest.mark.parametrize('momentum_change', [(True), (False)])
def test_evaluate_to_e2_trade(mocker, fcf_autotrageur, momentum_change):
    spread_opp = mocker.Mock()
    fcf_autotrageur.e2_targets = mocker.Mock()
    fcf_autotrageur.h_to_e1_max = mocker.Mock()
    fcf_autotrageur.trader1 = mocker.Mock()
    fcf_autotrageur.trader2 = mocker.Mock()
    mocker.patch.object(
        fcf_autotrageur, '_FCFAutotrageur__advance_target_index')
    mocker.patch.object(fcf_autotrageur, '_FCFAutotrageur__prepare_trade')
    mock_targets = mocker.Mock()
    mocker.patch.object(
        fcf_autotrageur, '_FCFAutotrageur__calc_targets', return_value=mock_targets)

    fcf_autotrageur._FCFAutotrageur__evaluate_to_e2_trade(
        momentum_change, spread_opp)

    fcf_autotrageur._FCFAutotrageur__advance_target_index.assert_called_with(
        spread_opp.e2_spread, fcf_autotrageur.e2_targets)
    fcf_autotrageur._FCFAutotrageur__prepare_trade.assert_called_with(
        momentum_change, fcf_autotrageur.trader1, fcf_autotrageur.trader2,
        fcf_autotrageur.e2_targets, spread_opp)
    fcf_autotrageur._FCFAutotrageur__calc_targets.assert_called_with(
        spread_opp.e1_spread, fcf_autotrageur.h_to_e1_max,
        fcf_autotrageur.trader2.quote_bal)
    assert fcf_autotrageur.e1_targets == mock_targets


@pytest.mark.parametrize('e1_spread, e2_spread, momentum, target_index', [
    (-3, 3, Momentum.NEUTRAL, 1),
    (3, -3, Momentum.NEUTRAL, 1),
    (-3, 3, Momentum.TO_E1, 1),
    (3, -3, Momentum.TO_E1, 1),
    (-3, 3, Momentum.TO_E2, 1),
    (3, -3, Momentum.TO_E2, 1),
    (-2, 0, Momentum.NEUTRAL, 1),
    (-2, 0, Momentum.TO_E1, 1),
    (-2, 0, Momentum.TO_E2, 1),
])
def test_evaluate_spread(
        mocker, fcf_autotrageur, e1_spread, e2_spread, momentum, target_index):
    # Setup fcf_autotrageur
    spread_opp = SpreadOpportunity(
        e1_spread, e2_spread, None, None, None, None)
    fcf_autotrageur.momentum = momentum
    fcf_autotrageur.target_index = target_index
    fcf_autotrageur.e1_targets = [(x, 1000 + 200*x) for x in range(-1, 4, 2)]
    fcf_autotrageur.e2_targets = [(x, 1000 + 200*x) for x in range(1, 10, 2)]
    mocker.patch.object(
        fcf_autotrageur, '_FCFAutotrageur__evaluate_to_e1_trade')
    mocker.patch.object(
        fcf_autotrageur, '_FCFAutotrageur__evaluate_to_e2_trade')

    # Execute test
    result = fcf_autotrageur._FCFAutotrageur__evaluate_spread(spread_opp)

    # Check results
    if momentum is Momentum.NEUTRAL:
        if e2_spread >= fcf_autotrageur.e2_targets[target_index][0]:
            assert result is True
            assert fcf_autotrageur.momentum is Momentum.TO_E2
            fcf_autotrageur._FCFAutotrageur__evaluate_to_e2_trade \
                .assert_called_with(True, spread_opp)
            return
        if e1_spread >= fcf_autotrageur.e1_targets[target_index][0]:
            assert result is True
            assert fcf_autotrageur.momentum is Momentum.TO_E1
            fcf_autotrageur._FCFAutotrageur__evaluate_to_e1_trade \
                .assert_called_with(True, spread_opp)
            return
    if momentum is Momentum.TO_E1:
        if e1_spread >= fcf_autotrageur.e1_targets[target_index][0]:
            assert result is True
            assert fcf_autotrageur.momentum is Momentum.TO_E1
            fcf_autotrageur._FCFAutotrageur__evaluate_to_e1_trade \
                .assert_called_with(False, spread_opp)
            return
        if e2_spread >= fcf_autotrageur.e2_targets[target_index][0]:
            assert result is True
            assert fcf_autotrageur.momentum is Momentum.TO_E2
            fcf_autotrageur._FCFAutotrageur__evaluate_to_e2_trade \
                .assert_called_with(True, spread_opp)
            return
    if momentum is Momentum.TO_E2:
        if e1_spread >= fcf_autotrageur.e1_targets[target_index][0]:
            assert result is True
            assert fcf_autotrageur.momentum is Momentum.TO_E1
            fcf_autotrageur._FCFAutotrageur__evaluate_to_e1_trade \
                .assert_called_with(True, spread_opp)
            return
        if e2_spread >= fcf_autotrageur.e2_targets[target_index][0]:
            assert result is True
            assert fcf_autotrageur.momentum is Momentum.TO_E2
            fcf_autotrageur._FCFAutotrageur__evaluate_to_e2_trade \
                .assert_called_with(False, spread_opp)
            return

    assert result is False


@pytest.mark.parametrize(
    'is_momentum_change, to_e1, target_index, last_target_index, '
    'buy_quote_balance, buy_price, sell_base_balance, result', [
        (True, True, 0, 0, 2000, 1000, 2,
            {'target_index': 1, 'last_target_index': 0, 'quote_target_amount': 1200}),
        (True, False, 0, 0, 2000, 1000, 2,
            {'target_index': 1, 'last_target_index': 0, 'quote_target_amount': 1200}),
        (False, True, 2, 0, 2000, 1000, 2,
            {'target_index': 3, 'last_target_index': 2, 'quote_target_amount': 800}),
        (False, False, 2, 0, 2000, 1000, 2,
            {'target_index': 3, 'last_target_index': 2, 'quote_target_amount': 800}),
        (True, True, 0, 0, 600, 1000, 2,
            {'target_index': 1, 'last_target_index': 0, 'quote_target_amount': 600}),
        (True, False, 0, 0, 600, 1000, 2,
            {'target_index': 1, 'last_target_index': 0, 'quote_target_amount': 600}),
        (False, True, 2, 0, 600, 1000, 2,
            {'target_index': 3, 'last_target_index': 2, 'quote_target_amount': 600}),
        (False, False, 2, 0, 600, 1000, 2,
            {'target_index': 3, 'last_target_index': 2, 'quote_target_amount': 600}),
        (True, True, 0, 0, 2000, 1000, 0.5, None),
        (True, False, 0, 0, 2000, 1000, 0.5, None),
        (False, True, 2, 0, 2000, 1000, 0.5, None),
        (False, False, 2, 0, 2000, 1000, 0.5, None),
        (True, True, 0, 0, 600, 1000, 0.5, None),
        (True, False, 0, 0, 600, 1000, 0.5, None),
        (False, True, 2, 0, 600, 1000, 0.5, None),
        (False, False, 2, 0, 600, 1000, 0.5, None),
    ])
def test_prepare_trade(mocker, fcf_autotrageur, is_momentum_change, to_e1,
                       target_index, last_target_index, buy_quote_balance,
                       buy_price, sell_base_balance, result):
    targets = [(x, 1000 + 200*x) for x in range(1, 10, 2)]
    spread_opp = mocker.Mock()
    spread_opp.e1_buy, spread_opp.e2_buy = buy_price, buy_price
    fcf_autotrageur.target_index = target_index
    fcf_autotrageur.last_target_index = last_target_index

    if to_e1:
        buy_trader = fcf_autotrageur.trader2
        sell_trader = fcf_autotrageur.trader1
    else:
        buy_trader = fcf_autotrageur.trader1
        sell_trader = fcf_autotrageur.trader2

    buy_trader.quote_bal = buy_quote_balance
    sell_trader.base_bal = sell_base_balance

    if result is None:
        with pytest.raises(InsufficientCryptoBalance):
            fcf_autotrageur._FCFAutotrageur__prepare_trade(
                is_momentum_change, buy_trader, sell_trader, targets,
                spread_opp)
        return

    fcf_autotrageur._FCFAutotrageur__prepare_trade(
        is_momentum_change, buy_trader, sell_trader, targets, spread_opp)

    sell_price_result = fcf_autotrageur.trade_metadata['sell_price']
    if to_e1:
        assert sell_price_result == spread_opp.e1_sell
    else:
        assert sell_price_result == spread_opp.e2_sell
    assert fcf_autotrageur.target_index == result['target_index']
    assert fcf_autotrageur.last_target_index == result['last_target_index']
    assert buy_trader.quote_target_amount == result['quote_target_amount']


@pytest.mark.parametrize('dryrun', [True, False])
@pytest.mark.parametrize('success', [True, False])
def test_execute_trade(mocker, fcf_autotrageur, dryrun, success):
    fcf_autotrageur.config[DRYRUN] = dryrun
    fcf_autotrageur.trade_metadata = mocker.Mock()
    mocker.patch.object(arbseeker, 'execute_arbitrage', return_value=success)
    mocker.patch.object(fcf_autotrageur.trader1, 'fetch_wallet_balances')
    mocker.patch.object(fcf_autotrageur.trader2, 'fetch_wallet_balances')

    fcf_autotrageur._execute_trade()

    arbseeker.execute_arbitrage.assert_called_with(     # pylint: disable=E1101
        fcf_autotrageur.trade_metadata)
    if not dryrun and success:
        fcf_autotrageur.trader1.fetch_wallet_balances.assert_called_once()
        fcf_autotrageur.trader2.fetch_wallet_balances.assert_called_once()
    else:
        fcf_autotrageur.trader1.fetch_wallet_balances.assert_not_called()
        fcf_autotrageur.trader2.fetch_wallet_balances.assert_not_called()


@pytest.mark.parametrize('vol_min', [100, 1000])
@pytest.mark.parametrize('e1_quote_balance', [0, 2000])
@pytest.mark.parametrize('e2_quote_balance', [0, 2000])
@pytest.mark.parametrize('network_error', [True, False])
@pytest.mark.parametrize('has_started', [True, False])
@pytest.mark.parametrize('e1_spread', [5, 50])
@pytest.mark.parametrize('e2_spread', [0, 3])
@pytest.mark.parametrize('h_to_e1_max', [5, 50])
@pytest.mark.parametrize('h_to_e2_max', [0, 3])
@pytest.mark.parametrize('is_opportunity', [True, False])
def test_poll_opportunity(mocker, no_patch_fcf_autotrageur, vol_min,
                          e1_quote_balance, e2_quote_balance, network_error,
                          has_started, e1_spread, e2_spread, h_to_e1_max,
                          h_to_e2_max, is_opportunity):
    no_patch_fcf_autotrageur.config = {
        'email_cfg_path': 'fake/path/to/config.yaml',
        'spread_target_low': 1.0,
        'spread_target_high': 5.0
    }
    trader1 = mocker.Mock()
    trader2 = mocker.Mock()
    mocker.patch.object(
        no_patch_fcf_autotrageur, 'trader1', trader1, create=True)
    mocker.patch.object(
        no_patch_fcf_autotrageur, 'trader2', trader2, create=True)
    no_patch_fcf_autotrageur.message = 'fake message'
    no_patch_fcf_autotrageur.vol_min = vol_min
    no_patch_fcf_autotrageur.trader1.quote_bal = e1_quote_balance
    no_patch_fcf_autotrageur.trader2.quote_bal = e2_quote_balance
    no_patch_fcf_autotrageur.has_started = has_started
    no_patch_fcf_autotrageur.h_to_e1_max = h_to_e1_max
    no_patch_fcf_autotrageur.h_to_e2_max = h_to_e2_max
    spread_opp = mocker.Mock()
    spread_opp.e1_spread = e1_spread
    spread_opp.e2_spread = e2_spread
    calc_targets = mocker.patch.object(no_patch_fcf_autotrageur,
                        '_FCFAutotrageur__calc_targets')
    evaluate_spread = mocker.patch.object(no_patch_fcf_autotrageur,
                        '_FCFAutotrageur__evaluate_spread',
                        return_value=is_opportunity)
    mocker.patch.object(
        arbseeker, 'get_spreads_by_ob', return_value=spread_opp)
    if network_error:
        arbseeker.get_spreads_by_ob.side_effect = NetworkError

    is_opportunity_result = no_patch_fcf_autotrageur._poll_opportunity()

    e1_result_target = no_patch_fcf_autotrageur.trader1.quote_target_amount
    e2_result_target = no_patch_fcf_autotrageur.trader2.quote_target_amount
    assert e1_result_target == max(vol_min, e1_quote_balance)
    assert e2_result_target == max(vol_min, e2_quote_balance)

    if network_error:
        assert is_opportunity_result is False
        calc_targets.assert_not_called()
        evaluate_spread.assert_not_called()
    else:
        if not has_started:
            assert no_patch_fcf_autotrageur.momentum == Momentum.NEUTRAL
            assert no_patch_fcf_autotrageur.target_index == 0
            assert no_patch_fcf_autotrageur.last_target_index == 0
            assert no_patch_fcf_autotrageur.has_started is True
            assert calc_targets.call_count == 2
            assert is_opportunity_result is False
            evaluate_spread.assert_not_called()
        else:
            evaluate_spread.assert_called_with(spread_opp)
            calc_targets.assert_not_called()
        assert no_patch_fcf_autotrageur.h_to_e1_max == max(h_to_e1_max, e1_spread)
        assert no_patch_fcf_autotrageur.h_to_e2_max == max(h_to_e2_max, e2_spread)


class TestEmailOrThrottle:
    def _setup_pre_email(self, mocker, fcf_autotrageur, fake_email_count,
                         fake_prev_spread, max_emails, rnding, tol):
        mock_send_all_emails = mocker.patch('bot.arbitrage.fcf_autotrageur.send_all_emails', autospec=True)
        mocker.patch('bot.arbitrage.fcf_autotrageur.email_count', fake_email_count)
        mocker.patch('bot.arbitrage.fcf_autotrageur.prev_spread', fake_prev_spread)

        fcf_autotrageur.config['max_emails'] = max_emails
        fcf_autotrageur.config['spread_rounding'] = rnding
        fcf_autotrageur.config['spread_tolerance'] = tol

        # Check before actual call made.
        assert bot.arbitrage.fcf_autotrageur.email_count == fake_email_count
        assert bot.arbitrage.fcf_autotrageur.prev_spread == fake_prev_spread

        return mock_send_all_emails

    @pytest.mark.parametrize('fake_email_count, next_email_count, fake_prev_spread, curr_spread, max_emails, rnding, tol', [
        (0, 1, Decimal('0.0'), Decimal('2.0'), 2, 1, 0.1),
        (1, 2, Decimal('2.0'), Decimal('2.0'), 2, 1, 0.1),
        (2, 1, Decimal('2.0'), Decimal('5.0'), 2, 1, 0.1)
    ])
    def test_FCFAutotrageur__email_or_throttle_emailed(self, mocker, fcf_autotrageur, fake_email_count,
                                       next_email_count, fake_prev_spread, curr_spread, max_emails,
                                       rnding, tol):
        mock_send_all_emails = self._setup_pre_email(mocker, fcf_autotrageur, fake_email_count,
            fake_prev_spread, max_emails, rnding, tol)

        fcf_autotrageur._FCFAutotrageur__email_or_throttle(curr_spread)
        assert mock_send_all_emails.called

        # Check email_count after actual call; should be incremented by 1.
        assert bot.arbitrage.fcf_autotrageur.email_count == next_email_count

    @pytest.mark.parametrize('fake_email_count, next_email_count, fake_prev_spread, curr_spread, max_emails, rnding, tol', [
        (0, 0, Decimal('0'), Decimal('0'), 0, 0, 0),
        pytest.param(0, 0, Decimal('0'), None, 0, 0, 0, marks=xfail(raises=(TypeError, InvalidOperation), reason="rounding or arithmetic on NoneType", strict=True)),
        (2, 2, Decimal('2.0'), Decimal('2.0'), 2, 1, 0.1),
        (2, 2, Decimal('2.0'), Decimal('2.1'), 2, 1, 0.1),
        (2, 2, Decimal('2.1'), Decimal('2.0'), 2, 1, 0.1)
    ])
    def test_FCFAutotrageur__email_or_throttle_throttled(self, mocker, fcf_autotrageur, fake_email_count,
                                         next_email_count, fake_prev_spread, curr_spread, max_emails,
                                         rnding, tol):
        mock_send_all_emails = self._setup_pre_email(mocker, fcf_autotrageur, fake_email_count,
            fake_prev_spread, max_emails, rnding, tol)

        fcf_autotrageur._FCFAutotrageur__email_or_throttle(curr_spread)
        assert not mock_send_all_emails.called

        # Check email_count after actual call; should not be incremented by 1.
        assert bot.arbitrage.fcf_autotrageur.email_count == next_email_count

# @pytest.mark.parametrize('opp_type', [
#     None,
#     SpreadOpportunity.LOW,
#     SpreadOpportunity.HIGH
# ])
# def test_FCFAutotrageur__set_message(mocker, fcf_autotrageur, opp_type):
#     mocker.patch.object(fcf_autotrageur, 'exchange1_basequote', ['BTC', 'USD'],
#         create=True)

#     fcf_autotrageur._FCFAutotrageur__set_message(opp_type)
#     if opp_type is SpreadOpportunity.LOW:
#         assert fcf_autotrageur.message == (
#                     EMAIL_LOW_SPREAD_HEADER
#                     + fcf_autotrageur.exchange1_basequote[0]
#                     + " is "
#                     + str(fcf_autotrageur.spread_opp[arbseeker.SPREAD]))
#     elif opp_type is SpreadOpportunity.HIGH:
#         assert fcf_autotrageur.message == (
#                     EMAIL_HIGH_SPREAD_HEADER
#                     + fcf_autotrageur.exchange1_basequote[0]
#                     + " is "
#                     + str(fcf_autotrageur.spread_opp[arbseeker.SPREAD]))
#     elif opp_type is None:
#         assert fcf_autotrageur.message == EMAIL_NONE_SPREAD
#     else:
#         pytest.fail('Unsupported spread opportunity type.')


def test_clean_up(fcf_autotrageur):
    assert fcf_autotrageur.message == 'fake message'
    # assert fcf_autotrageur.spread_opp == { arbseeker.SPREAD: 1.0 }
    fcf_autotrageur._clean_up()
    assert fcf_autotrageur.message is None


def test_setup_markets(mocker, fcf_autotrageur):
    import builtins
    s = mocker.patch.object(builtins, 'super')
    fcf_autotrageur.config = {
        SPREAD_MIN: 2,
        VOL_MIN: 1000,
        H_TO_E1_MAX: 3,
        H_TO_E2_MAX: 50
    }

    fcf_autotrageur._setup_markets()

    s.assert_called_once()
    assert fcf_autotrageur.spread_min == Decimal('2')
    assert fcf_autotrageur.vol_min == Decimal('1000')
    assert fcf_autotrageur.h_to_e1_max == Decimal('3')
    assert fcf_autotrageur.h_to_e2_max == Decimal('50')
