from decimal import Decimal

import pytest
import schedule

import libs.utils.schedule_utils as schedule_utils
from bot.arbitrage.fcf_autotrageur import FCFBalanceChecker


@pytest.fixture
def balance_checker(mocker):
    trader1 = mocker.Mock()
    trader2 = mocker.Mock()
    is_dry_run = False
    notification_func = mocker.Mock()
    return FCFBalanceChecker(trader1, trader2, is_dry_run, notification_func)

def test_init(mocker):
    trader1 = mocker.Mock()
    trader2 = mocker.Mock()
    is_dry_run = False
    notification_func = mocker.Mock()

    result = FCFBalanceChecker(trader1, trader2, is_dry_run, notification_func)

    assert result.trader1 == trader1
    assert result.trader2 == trader2
    assert result.is_dry_run == is_dry_run
    assert result.notification_func == notification_func
    assert result.crypto_balance_low == False


@pytest.mark.parametrize(
    'buy_price, buy_volume, sell_balance, sell_exchange, base, expected_results', [
        (Decimal('300'), Decimal('600'), Decimal('2'), 'bithumb', 'ETH', []),
        (Decimal('300'), Decimal('600'), Decimal('2.1'), 'bithumb', 'ETH', []),
        (Decimal('300'), Decimal('500'), Decimal('2'), 'bithumb', 'ETH', []),
        (Decimal('300'), Decimal('700'), Decimal('2'), 'bithumb', 'ETH', ['2.333333333333', 'bithumb', 'ETH']),
        (Decimal('300'), Decimal('700'), Decimal('2'), 'kraken', 'BTC', ['2.333333333333', 'kraken', 'BTC']),
        (Decimal('500'), Decimal('800'), Decimal('1.5'), 'bithumb', 'ETH', ['1.6', 'bithumb', 'ETH']),
        (Decimal('500'), Decimal('800'), Decimal('1.5'), 'kraken', 'BTC', ['1.6', 'kraken', 'BTC']),
    ])
def test_create_low_balance_msg(
        balance_checker, buy_price, buy_volume, sell_balance, sell_exchange,
        base, expected_results):
    result = balance_checker._FCFBalanceChecker__create_low_balance_msg(
        buy_price, buy_volume, sell_balance, sell_exchange, base)

    for expected_result in expected_results:
        assert expected_result in result


def test_send_balance_warning(mocker, balance_checker):
    mocker.patch.object(
        balance_checker, 'low_balance_message', 'Some message', create=True)
    balance_checker._FCFBalanceChecker__send_balance_warning()
    balance_checker.notification_func.assert_called_once_with(
        "SELL SIDE BALANCE BELOW THRESHOLD",
        balance_checker.low_balance_message)


@pytest.mark.parametrize('e1_message', ['Some e1 message', None])
@pytest.mark.parametrize('e2_message', ['Some e2 message', None])
@pytest.mark.parametrize('crypto_balance_low', [True, False])
def test_check_crypto_balances(mocker, balance_checker, e1_message, e2_message, crypto_balance_low):
    mocker.patch.object(balance_checker,
                        '_FCFBalanceChecker__create_low_balance_msg',
                        side_effect=[e1_message, e2_message])
    mock_every = mocker.patch.object(schedule, 'every')
    mock_clear = mocker.patch.object(schedule, 'clear')
    mock_fetch_job = mocker.patch.object(schedule_utils, 'fetch_only_job')
    balance_checker.crypto_balance_low = crypto_balance_low

    balance_checker.check_crypto_balances(mocker.Mock())

    if e1_message or e2_message:
        assert balance_checker.crypto_balance_low
        balance_checker.trader1.update_wallet_balances.assert_called_once()
        balance_checker.trader2.update_wallet_balances.assert_called_once()
        if not crypto_balance_low:
            mock_every.assert_called_once_with(1)
            mock_fetch_job.assert_called_once_with(
                balance_checker.CRYPTO_BELOW_THRESHOLD_SCHEDULE_TAG)
    else:
        assert not balance_checker.crypto_balance_low
        mock_clear.assert_called_once()

