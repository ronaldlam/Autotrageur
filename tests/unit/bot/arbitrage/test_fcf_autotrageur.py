# pylint: disable=E1101
import copy
from decimal import Decimal, InvalidOperation

import pytest
from ccxt import NetworkError, ExchangeError

import bot.arbitrage.arbseeker as arbseeker
import bot.arbitrage.fcf_autotrageur
from libs.email_client.simple_email_client import send_all_emails
from libs.utilities import num_to_decimal
from bot.arbitrage.arbseeker import SpreadOpportunity
from bot.arbitrage.fcf_autotrageur import (EMAIL_HIGH_SPREAD_HEADER,
                                           EMAIL_LOW_SPREAD_HEADER,
                                           EMAIL_NONE_SPREAD, FCFAutotrageur,
                                           FCFCheckpoint,
                                           InsufficientCryptoBalance,
                                           IncompleteArbitrageError,
                                           arbseeker, email_count, prev_spread)
from bot.common.config_constants import (DRYRUN, H_TO_E1_MAX, H_TO_E2_MAX,
                                         SPREAD_MIN, VOL_MIN, EMAIL_CFG_PATH)
from bot.common.enums import Momentum

xfail = pytest.mark.xfail


# Test constants.
FAKE_BUY_PRICE = num_to_decimal(100.99)
FAKE_SELL_PRICE = num_to_decimal(105.99)
FAKE_PRE_FEE_BASE = num_to_decimal(10.00)
FAKE_PRE_FEE_QUOTE = num_to_decimal(100.99)
FAKE_POST_FEE_BASE = num_to_decimal(10.00)
FAKE_POST_FEE_QUOTE = num_to_decimal(100.99)

FAKE_UNIFIED_RESPONSE = {
    'pre_fee_base': FAKE_PRE_FEE_BASE,
    'pre_fee_quote': FAKE_PRE_FEE_QUOTE,
    'post_fee_base': FAKE_POST_FEE_BASE,
    'post_fee_quote': FAKE_POST_FEE_QUOTE
}

FAKE_UNIFIED_RESPONSE_DIFFERENT_AMOUNT = {
    'pre_fee_base': num_to_decimal(101.99),
    'pre_fee_quote': FAKE_PRE_FEE_QUOTE,
    'post_fee_base': FAKE_POST_FEE_BASE,
    'post_fee_quote': FAKE_POST_FEE_QUOTE
}

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
    f.trade_metadata = {}
    trader1 = fake_ccxt_trader
    trader2 = copy.deepcopy(fake_ccxt_trader)
    mocker.patch.object(f, 'trader1', trader1, create=True)
    mocker.patch.object(f, 'trader2', trader2, create=True)
    return f


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
        mocker, no_patch_fcf_autotrageur, spread, start, result):
    # Chosen for the roughly round numbers.
    targets = [(x, 1000 + 200*x) for x in range(-1, 10, 2)]
    mocker.patch.object(
        no_patch_fcf_autotrageur, 'target_index', start, create=True)
    no_patch_fcf_autotrageur._FCFAutotrageur__advance_target_index(
        spread, targets)
    assert no_patch_fcf_autotrageur.target_index == result


@pytest.mark.parametrize(
    'vol_min, spread, h_max, from_balance, result', [
        (Decimal('1000'), Decimal('4'), Decimal('2'), Decimal('1000'),
            [(Decimal('5'), Decimal('1000'))]), # spread + spread_min > h_max, vol_min == from_balance
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
def test_calc_targets(mocker, no_patch_fcf_autotrageur, vol_min, spread, h_max,
                      from_balance, result):
    mocker.patch.object(
        no_patch_fcf_autotrageur, 'spread_min', Decimal('1'), create=True)
    mocker.patch.object(
        no_patch_fcf_autotrageur, 'vol_min', vol_min, create=True)
    targets = no_patch_fcf_autotrageur._FCFAutotrageur__calc_targets(
        spread, h_max, from_balance)
    assert targets == result


@pytest.mark.parametrize('momentum_change', [True, False])
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


@pytest.mark.parametrize('momentum_change', [True, False])
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
def test_evaluate_spread(
        mocker, fcf_autotrageur, e1_spread, e2_spread, momentum, target_index):
    # Setup fcf_autotrageur
    spread_opp = SpreadOpportunity(
        e1_spread, e2_spread, None, None, None, None)
    mocker.patch.object(fcf_autotrageur, 'momentum', momentum, create=True)
    mocker.patch.object(fcf_autotrageur, 'target_index', target_index, create=True)
    # Chosen for the roughly round numbers.
    e1_targets = [(Decimal(x), Decimal(1000 + 200*x)) for x in range(-1, 4, 2)]
    e2_targets = [(Decimal(x), Decimal(1000 + 200*x)) for x in range(1, 10, 2)]
    mocker.patch.object(fcf_autotrageur, 'e1_targets', e1_targets, create=True)
    mocker.patch.object(fcf_autotrageur, 'e2_targets', e2_targets, create=True)
    mocker.patch.object(
        fcf_autotrageur, '_FCFAutotrageur__evaluate_to_e1_trade')
    mocker.patch.object(
        fcf_autotrageur, '_FCFAutotrageur__evaluate_to_e2_trade')

    # Execute test
    if e1_spread is None or e2_spread is None:
        with pytest.raises(TypeError):
            fcf_autotrageur._FCFAutotrageur__evaluate_spread(spread_opp)
        return
    else:
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
        (False, False, 2, 0, Decimal('2000'), Decimal('1000'), Decimal('0.5'), None),
        (True, True, 0, 0, Decimal('600'), Decimal('1000'), Decimal('0.5'), None),
        (True, False, 0, 0, Decimal('600'), Decimal('1000'), Decimal('0.5'), None),
        (False, True, 2, 0, Decimal('600'), Decimal('1000'), Decimal('0.5'), None),
        (False, False, 2, 0, Decimal('600'), Decimal('1000'), Decimal('0.5'), None),
    ])
def test_prepare_trade(mocker, fcf_autotrageur, is_momentum_change, to_e1,
                       target_index, last_target_index, buy_quote_balance,
                       buy_price, sell_base_balance, result):
    # Chosen for the roughly round numbers.
    targets = [(x, 1000 + 200*x) for x in range(1, 10, 2)]
    spread_opp = mocker.Mock()
    spread_opp.e1_buy, spread_opp.e2_buy = buy_price, buy_price
    mocker.patch.object(
        fcf_autotrageur, 'target_index', target_index, create=True)
    mocker.patch.object(
        fcf_autotrageur, 'last_target_index', last_target_index, create=True)

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


class TestExecuteTrade:
    def _setup_mocks(self, mocker, fake_ccxt_trader, no_patch_fcf_autotrageur, dryrun):
        trader1 = fake_ccxt_trader
        trader2 = copy.deepcopy(fake_ccxt_trader)
        mocker.patch.object(no_patch_fcf_autotrageur, 'trader1', trader1, create=True)
        mocker.patch.object(no_patch_fcf_autotrageur, 'trader2', trader2, create=True)
        mocker.patch.object(
            no_patch_fcf_autotrageur, 'config', { DRYRUN: dryrun }, create=True)
        mocker.patch.object(
            no_patch_fcf_autotrageur, 'checkpoint', FCFCheckpoint(), create=True)
        mocker.patch.object(no_patch_fcf_autotrageur.checkpoint, 'restore')
        mocker.patch.object(no_patch_fcf_autotrageur, 'trade_metadata', {
            'buy_price': FAKE_BUY_PRICE,
            'sell_price': FAKE_SELL_PRICE,
            'buy_trader': no_patch_fcf_autotrageur.trader1,
            'sell_trader': no_patch_fcf_autotrageur.trader2
        }, create=True)
        mocker.patch.object(
            arbseeker, 'execute_buy', return_value=FAKE_UNIFIED_RESPONSE)
        mocker.patch.object(
            arbseeker, 'execute_sell', return_value=FAKE_UNIFIED_RESPONSE)
        mocker.patch.object(no_patch_fcf_autotrageur.trader1, 'fetch_wallet_balances')
        mocker.patch.object(no_patch_fcf_autotrageur.trader2, 'fetch_wallet_balances')

    @pytest.mark.parametrize('dryrun', [True, False])
    def test_execute_trade(self, mocker, fake_ccxt_trader, no_patch_fcf_autotrageur, dryrun):
        self._setup_mocks(mocker, fake_ccxt_trader, no_patch_fcf_autotrageur, dryrun)
        no_patch_fcf_autotrageur._execute_trade()

        arbseeker.execute_buy.assert_called_once_with(
            no_patch_fcf_autotrageur.trade_metadata['buy_trader'],
            no_patch_fcf_autotrageur.trade_metadata['buy_price'])
        arbseeker.execute_sell.assert_called_once_with(
            no_patch_fcf_autotrageur.trade_metadata['sell_trader'],
            no_patch_fcf_autotrageur.trade_metadata['sell_price'],
            FAKE_UNIFIED_RESPONSE['post_fee_base'])
        if not dryrun:
            no_patch_fcf_autotrageur.trader1.fetch_wallet_balances.assert_called_once()
            no_patch_fcf_autotrageur.trader2.fetch_wallet_balances.assert_called_once()
        else:
            no_patch_fcf_autotrageur.trader1.fetch_wallet_balances.assert_not_called()
            no_patch_fcf_autotrageur.trader2.fetch_wallet_balances.assert_not_called()

    @pytest.mark.parametrize('exc_type', [
        ExchangeError,
        Exception
    ])
    def test_execute_trade_buy_exchange_err(self, mocker, fake_ccxt_trader,
                                            no_patch_fcf_autotrageur, exc_type):
        self._setup_mocks(mocker, fake_ccxt_trader, no_patch_fcf_autotrageur, False)
        arbseeker.execute_buy.side_effect = exc_type
        no_patch_fcf_autotrageur._execute_trade()

        no_patch_fcf_autotrageur.checkpoint.restore.assert_called_once()
        arbseeker.execute_buy.assert_called_once_with(
            no_patch_fcf_autotrageur.trade_metadata['buy_trader'],
            no_patch_fcf_autotrageur.trade_metadata['buy_price'])
        arbseeker.execute_sell.assert_not_called()
        no_patch_fcf_autotrageur.trader1.fetch_wallet_balances.assert_not_called()
        no_patch_fcf_autotrageur.trader2.fetch_wallet_balances.assert_not_called()

    @pytest.mark.parametrize('exc_type', [
        ExchangeError,
        Exception,
        IncompleteArbitrageError
    ])
    def test_execute_trade_sell_error(self, mocker, fake_ccxt_trader,
                                      no_patch_fcf_autotrageur, exc_type):
        self._setup_mocks(mocker, fake_ccxt_trader, no_patch_fcf_autotrageur, False)
        mocker.patch.object(no_patch_fcf_autotrageur, '_send_email')

        if exc_type is IncompleteArbitrageError:
            arbseeker.execute_sell.return_value = FAKE_UNIFIED_RESPONSE_DIFFERENT_AMOUNT
        else:
            arbseeker.execute_sell.side_effect = exc_type

        with pytest.raises(exc_type):
            no_patch_fcf_autotrageur._execute_trade()

        arbseeker.execute_buy.assert_called_once_with(
            no_patch_fcf_autotrageur.trade_metadata['buy_trader'],
            no_patch_fcf_autotrageur.trade_metadata['buy_price'])
        arbseeker.execute_sell.assert_called_once_with(
            no_patch_fcf_autotrageur.trade_metadata['sell_trader'],
            no_patch_fcf_autotrageur.trade_metadata['sell_price'],
            FAKE_UNIFIED_RESPONSE['post_fee_base'])
        no_patch_fcf_autotrageur.checkpoint.restore.assert_not_called()
        no_patch_fcf_autotrageur._send_email.assert_called_once()
        no_patch_fcf_autotrageur.trader1.fetch_wallet_balances.assert_not_called()
        no_patch_fcf_autotrageur.trader2.fetch_wallet_balances.assert_not_called()


@pytest.mark.parametrize('vol_min', [Decimal('100'), Decimal('1000')])
@pytest.mark.parametrize('e1_quote_balance', [Decimal('0'), Decimal('2000')])
@pytest.mark.parametrize('e2_quote_balance', [Decimal('0'), Decimal('2000')])
@pytest.mark.parametrize('network_error', [True, False])
@pytest.mark.parametrize('has_started', [True, False])
@pytest.mark.parametrize('e1_spread', [Decimal('5'), Decimal('50')])
@pytest.mark.parametrize('e2_spread', [Decimal('0'), Decimal('3')])
@pytest.mark.parametrize('h_to_e1_max', [Decimal('5'), Decimal('50')])
@pytest.mark.parametrize('h_to_e2_max', [Decimal('0'), Decimal('3')])
@pytest.mark.parametrize('is_opportunity', [True, False])
def test_poll_opportunity(mocker, no_patch_fcf_autotrageur, vol_min,
                          e1_quote_balance, e2_quote_balance, network_error,
                          has_started, e1_spread, e2_spread, h_to_e1_max,
                          h_to_e2_max, is_opportunity):
    trader1 = mocker.Mock()
    trader2 = mocker.Mock()
    mocker.patch.object(
        no_patch_fcf_autotrageur, 'checkpoint', FCFCheckpoint(), create=True)
    mocker.patch.object(no_patch_fcf_autotrageur.checkpoint, 'save')
    mocker.patch.object(
        no_patch_fcf_autotrageur, 'trader1', trader1, create=True)
    mocker.patch.object(
        no_patch_fcf_autotrageur, 'trader2', trader2, create=True)
    no_patch_fcf_autotrageur.trader1.quote_bal = e1_quote_balance
    no_patch_fcf_autotrageur.trader2.quote_bal = e2_quote_balance
    mocker.patch.object(
        no_patch_fcf_autotrageur, 'vol_min', vol_min, create=True)
    mocker.patch.object(
        no_patch_fcf_autotrageur, 'has_started', has_started, create=True)
    mocker.patch.object(
        no_patch_fcf_autotrageur, 'h_to_e1_max', h_to_e1_max, create=True)
    mocker.patch.object(
        no_patch_fcf_autotrageur, 'h_to_e2_max', h_to_e2_max, create=True)
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
            no_patch_fcf_autotrageur.checkpoint.save.assert_called_once_with(
                no_patch_fcf_autotrageur)
            evaluate_spread.assert_called_with(spread_opp)
            calc_targets.assert_not_called()
        assert no_patch_fcf_autotrageur.h_to_e1_max == max(h_to_e1_max, e1_spread)
        assert no_patch_fcf_autotrageur.h_to_e2_max == max(h_to_e2_max, e2_spread)


def test_clean_up(fcf_autotrageur):
    fcf_autotrageur._clean_up()
    assert fcf_autotrageur.trade_metadata is None


def test_send_email(mocker, no_patch_fcf_autotrageur):
    FAKE_SUBJECT = 'A FAKE SUBJECT'
    FAKE_MESSAGE = 'A FAKE MESSAGE'

    mocker.patch.object(no_patch_fcf_autotrageur, 'config', {
        EMAIL_CFG_PATH: 'path/to/config'
    }, create=True)
    mocker.patch('bot.arbitrage.fcf_autotrageur.send_all_emails')
    no_patch_fcf_autotrageur._send_email(FAKE_SUBJECT, FAKE_MESSAGE)
    bot.arbitrage.fcf_autotrageur.send_all_emails.assert_called_once_with(
        no_patch_fcf_autotrageur.config[EMAIL_CFG_PATH],
        'Subject: {}\n{}'.format(FAKE_SUBJECT, FAKE_MESSAGE)
    )


def test_setup(mocker, fcf_autotrageur):
    import builtins
    s = mocker.patch.object(builtins, 'super')
    mocker.patch.dict(fcf_autotrageur.config, {
        SPREAD_MIN: 2,
        VOL_MIN: 1000,
        H_TO_E1_MAX: 3,
        H_TO_E2_MAX: 50
    })

    fcf_autotrageur._setup()

    s.assert_called_once()
    assert fcf_autotrageur.spread_min == Decimal('2')
    assert fcf_autotrageur.vol_min == Decimal('1000')
    assert fcf_autotrageur.h_to_e1_max == Decimal('3')
    assert fcf_autotrageur.h_to_e2_max == Decimal('50')
    assert isinstance(fcf_autotrageur.checkpoint, FCFCheckpoint)
