import copy
from unittest.mock import MagicMock

import pytest

import autotrageur.bot.arbitrage.fcf.fcf_checkpoint_utils as fcf_checkpoint_utils
from autotrageur.bot.arbitrage.fcf.fcf_checkpoint import (CURRENT_FCF_CHECKPOINT_VERSION,
                                                          FCFCheckpoint)

MOCK_CONFIG = MagicMock()
MOCK_CURRENT_VERSION = '9.99.99'
MOCK_STRATEGY_STATE = MagicMock()
MOCK_STAT_TRACKER = MagicMock()
MOCK_CHECKPOINT_KWARGS_FULL = {
    'config': MOCK_CONFIG,
    'strategy_state': MOCK_STRATEGY_STATE,
    'stat_tracker': MOCK_STAT_TRACKER,
    'version': MOCK_CURRENT_VERSION
}
MOCK_CHECKPOINT_KWARGS_PRE112 = {
    'config': MOCK_CONFIG,
    'strategy_state': MOCK_STRATEGY_STATE,
    'dry_run_manager': MagicMock(),
    'version': '1.1.1'
}

@pytest.fixture(scope='module')
def mock_fcf_checkpoint():
    return FCFCheckpoint(
        config=MOCK_CONFIG,
        strategy_state=MOCK_STRATEGY_STATE,
        stat_tracker=MOCK_STAT_TRACKER)


def test_form_fcf_attr_map(mocker, mock_fcf_checkpoint):
    attr_map = fcf_checkpoint_utils._form_fcf_attr_map(mock_fcf_checkpoint)
    assert attr_map == {
    'config': MOCK_CONFIG,
    'strategy_state': MOCK_STRATEGY_STATE,
    'stat_tracker': MOCK_STAT_TRACKER
}


def test_pickle_fcf_checkpoint(mocker, mock_fcf_checkpoint):
    FAKE_ATTR_MAP = {
        'fake': 'stuff'
    }
    mock_form_attr_map = mocker.patch.object(
        fcf_checkpoint_utils,
        '_form_fcf_attr_map',
        return_value=FAKE_ATTR_MAP)

    result = fcf_checkpoint_utils.pickle_fcf_checkpoint(mock_fcf_checkpoint)

    mock_form_attr_map.assert_called_with(mock_fcf_checkpoint)
    assert FAKE_ATTR_MAP['version'] == str(CURRENT_FCF_CHECKPOINT_VERSION)
    assert result == (fcf_checkpoint_utils.unpickle_fcf_checkpoint, (FAKE_ATTR_MAP,))


def test_unpickle_fcf_checkpoint(mocker):
    MOCK_CHECKPOINT_KWARGS_FULL_COPY = copy.deepcopy(MOCK_CHECKPOINT_KWARGS_FULL)
    result = fcf_checkpoint_utils.unpickle_fcf_checkpoint(MOCK_CHECKPOINT_KWARGS_FULL_COPY)
    assert isinstance(result, FCFCheckpoint)
    assert fcf_checkpoint_utils._form_fcf_attr_map(result) == MOCK_CHECKPOINT_KWARGS_FULL_COPY


def test_unpickle_fcf_checkpoint_pre112(mocker):
    MOCK_PRE112_KWARGS_COPY = copy.deepcopy(MOCK_CHECKPOINT_KWARGS_PRE112)
    assert MOCK_PRE112_KWARGS_COPY.get('dry_run_manager') is not None
    result = fcf_checkpoint_utils.unpickle_fcf_checkpoint(MOCK_PRE112_KWARGS_COPY)
    assert isinstance(result, FCFCheckpoint)
    # Check that the Checkpoint constructs.
    assert fcf_checkpoint_utils._form_fcf_attr_map(result) == {
        'config': MOCK_CONFIG,
        'strategy_state': MOCK_STRATEGY_STATE,
        'stat_tracker': None
    }
