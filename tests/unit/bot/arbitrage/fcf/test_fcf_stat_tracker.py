from unittest.mock import Mock

import pytest

from autotrageur.bot.arbitrage.fcf.fcf_stat_tracker import FCFStatTracker

FAKE_NEW_ID = Mock()
FAKE_E1_TRADER = Mock()
FAKE_E2_TRADER = Mock()
FAKE_DRY_RUN_E1 = Mock()
FAKE_DRY_RUN_E2 = Mock()


@pytest.fixture(scope='module')
def mock_fcf_stat_tracker():
    return FCFStatTracker(FAKE_NEW_ID, FAKE_E1_TRADER, FAKE_E2_TRADER)


def test_init(mocker):
    mocker.patch.object(FAKE_E1_TRADER, 'dry_run_exchange', FAKE_DRY_RUN_E1)
    mocker.patch.object(FAKE_E2_TRADER, 'dry_run_exchange', FAKE_DRY_RUN_E2)
    stat_tracker = FCFStatTracker(FAKE_NEW_ID, FAKE_E1_TRADER, FAKE_E2_TRADER)
    assert stat_tracker.id is FAKE_NEW_ID
    assert stat_tracker.e1 is FAKE_E1_TRADER
    assert stat_tracker.e2 is FAKE_E2_TRADER
    assert stat_tracker.dry_run_e1 is FAKE_DRY_RUN_E1
    assert stat_tracker.dry_run_e2 is FAKE_DRY_RUN_E2
    assert stat_tracker.trade_count == 0


def test_attach_traders(mocker, mock_fcf_stat_tracker):
    del mock_fcf_stat_tracker.e1
    del mock_fcf_stat_tracker.e2
    assert not hasattr(mock_fcf_stat_tracker, 'e1')
    assert not hasattr(mock_fcf_stat_tracker, 'e2')

    mock_fcf_stat_tracker.attach_traders(FAKE_E1_TRADER, FAKE_E2_TRADER)

    assert mock_fcf_stat_tracker.e1 == FAKE_E1_TRADER
    assert mock_fcf_stat_tracker.e2 == FAKE_E2_TRADER


def test_detach_traders(mocker, mock_fcf_stat_tracker):
    assert hasattr(mock_fcf_stat_tracker, 'e1')
    assert hasattr(mock_fcf_stat_tracker, 'e2')

    mock_fcf_stat_tracker.detach_traders()

    assert not hasattr(mock_fcf_stat_tracker, 'e1')
    assert not hasattr(mock_fcf_stat_tracker, 'e2')
