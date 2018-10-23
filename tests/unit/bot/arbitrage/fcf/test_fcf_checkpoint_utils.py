from unittest.mock import MagicMock

import pytest

import autotrageur.bot.arbitrage.fcf.fcf_checkpoint_utils as fcf_checkpoint_utils
from autotrageur.bot.arbitrage.fcf.fcf_checkpoint import (CURRENT_FCF_CHECKPOINT_VERSION,
                                              FCFCheckpoint)

MOCK_CONFIG = MagicMock()
MOCK_STRATEGY_STATE = MagicMock()
MOCK_DRY_RUN_MANAGER = MagicMock()
MOCK_CHECKPOINT_KWARGS = {
    'config': MOCK_CONFIG,
    'strategy_state': MOCK_STRATEGY_STATE,
    'dry_run_manager': MOCK_DRY_RUN_MANAGER
}

@pytest.fixture(scope='module')
def mock_fcf_checkpoint():
    return FCFCheckpoint(
        config=MOCK_CONFIG,
        strategy_state=MOCK_STRATEGY_STATE,
        dry_run_manager=MOCK_DRY_RUN_MANAGER)


def test_form_fcf_attr_map(mocker, mock_fcf_checkpoint):
    attr_map = fcf_checkpoint_utils._form_fcf_attr_map(mock_fcf_checkpoint)
    assert attr_map == MOCK_CHECKPOINT_KWARGS


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
    assert FAKE_ATTR_MAP['version'] == CURRENT_FCF_CHECKPOINT_VERSION
    assert result == (fcf_checkpoint_utils.unpickle_fcf_checkpoint, (FAKE_ATTR_MAP,))


def test_unpickle_fcf_checkpoint(mocker):
    result = fcf_checkpoint_utils.unpickle_fcf_checkpoint(MOCK_CHECKPOINT_KWARGS)
    assert isinstance(result, FCFCheckpoint)
    assert fcf_checkpoint_utils._form_fcf_attr_map(result) == MOCK_CHECKPOINT_KWARGS


