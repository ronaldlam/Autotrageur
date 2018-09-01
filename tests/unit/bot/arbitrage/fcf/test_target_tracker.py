import pytest

from bot.arbitrage.fcf.target_tracker import FCFTargetTracker


@pytest.fixture(scope='module')
def fcf_target_tracker():
    return FCFTargetTracker()

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
        mocker, fcf_target_tracker, spread, start, result):
    # Chosen for the roughly round numbers.
    targets = [(x, 1000 + 200*x) for x in range(-1, 10, 2)]
    mocker.patch.object(
        fcf_target_tracker, '_target_index', start, create=True)
    fcf_target_tracker.advance_target_index(
        spread, targets)
    assert fcf_target_tracker._target_index == result
