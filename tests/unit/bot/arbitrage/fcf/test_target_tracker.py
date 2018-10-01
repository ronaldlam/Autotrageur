import pytest

from bot.arbitrage.fcf.target_tracker import FCFTargetTracker


@pytest.fixture(scope='module')
def fcf_target_tracker():
    return FCFTargetTracker()


@pytest.fixture(scope='module')
def targets():
    # Chosen for the roughly round numbers.
    return [(x, 1000 + 200*x) for x in range(-1, 10, 2)]


def test_init():
    result = FCFTargetTracker()
    assert result._target_index == 0
    assert result._last_target_index == 0


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
        mocker, fcf_target_tracker, targets, spread, start, result):
    mocker.patch.object(fcf_target_tracker, '_target_index', start)
    fcf_target_tracker.advance_target_index(
        spread, targets)
    assert fcf_target_tracker._target_index == result


def test_reset_target_index(fcf_target_tracker):
    fcf_target_tracker.reset_target_index()
    assert fcf_target_tracker._target_index == 0
    assert fcf_target_tracker._last_target_index == 0


@pytest.mark.parametrize(
    'target_index, last_target_index, is_momentum_change, expected_result', [
        (0, 0, True, 800),
        (0, 0, False, 800),
        (3, 0, True, 2000),
        (3, 0, False, 1200),
        (0, 3, True, 800),
        (0, 3, False, 800),     # Should be impossible, decrease in index w/ no momentum change.
        (4, 1, True, 2400),
        (4, 1, False, 1200),
        (1, 4, True, 1200),
        (1, 4, False, -1200),   # Should be impossible, decrease in index w/ no momentum change.
    ])
def test_get_trade_volume(
        mocker, fcf_target_tracker, targets, target_index, last_target_index,
        is_momentum_change, expected_result):
    mocker.patch.object(fcf_target_tracker, '_target_index', target_index)
    mocker.patch.object(fcf_target_tracker, '_last_target_index', last_target_index)

    result = fcf_target_tracker.get_trade_volume(targets, is_momentum_change)

    assert result == expected_result


@pytest.mark.parametrize(
    'target_index, spread, is_momentum_change, expected_result', [
        (1, 2, False, True),
        (1, 2, True, True),
        (2, 2, False, False),
        (2, 2, True, True),
        (6, 10, False, False),
        (6, 10, True, True),
    ])
def test_has_hit_targets(
        mocker, fcf_target_tracker, targets, target_index, spread,
        is_momentum_change, expected_result):
    mocker.patch.object(fcf_target_tracker, '_target_index', target_index)

    result = fcf_target_tracker.has_hit_targets(
        spread, targets, is_momentum_change)

    assert result == expected_result


@pytest.mark.parametrize(
    'target_index, last_target_index', [
        (3, 4), (0, 1234), (42, 0), (0, 0)
    ]
)
def test_increment(mocker, fcf_target_tracker, target_index, last_target_index):
    mocker.patch.object(fcf_target_tracker, '_target_index', target_index)
    mocker.patch.object(fcf_target_tracker, '_last_target_index', last_target_index)

    fcf_target_tracker.increment()

    assert fcf_target_tracker._target_index == target_index + 1
    assert fcf_target_tracker._last_target_index == target_index
