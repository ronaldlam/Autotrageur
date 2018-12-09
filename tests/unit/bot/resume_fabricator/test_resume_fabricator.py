import copy
import getpass
import os
import sys
from decimal import Decimal

import pytest
import yaml

import autotrageur.resume_fabricator as rf
from autotrageur.bot.arbitrage.fcf.configuration import FCFConfiguration
from autotrageur.bot.arbitrage.fcf.fcf_checkpoint import FCFCheckpoint
from autotrageur.bot.arbitrage.fcf.strategy import FCFStrategyState
from autotrageur.bot.arbitrage.fcf.target_tracker import FCFTargetTracker
from autotrageur.bot.arbitrage.trade_chunker import TradeChunker
from autotrageur.bot.common.enums import Momentum
from fp_libs.utilities import num_to_decimal

CURR_DIR = os.path.dirname(os.path.realpath(__file__))

# Mocked loaded config.
MOCK_CONFIG_ID = 'some_uuid_uuid4'
MOCK_STARTING_TS = 12345678
MOCK_STARTING_CONFIG = FCFConfiguration(
    id=MOCK_CONFIG_ID,
    start_timestamp=MOCK_STARTING_TS,
    dryrun=False,
    dryrun_e1_base='ETH',
    dryrun_e1_quote='USD',
    dryrun_e2_base='ETH',
    dryrun_e2_quote='KRW',
    email_cfg_path='path/to/email',
    exchange1='kraken',
    exchange1_pair='ETH/USD',
    exchange2='bithumb',
    exchange2_pair='ETH/KRW',
    use_test_api=False,
    h_to_e1_max=100,
    h_to_e2_max=50,
    max_trade_size=5,
    poll_wait_default=60,
    poll_wait_short=6,
    slippage=3,
    spread_min=1.4,
    twilio_cfg_path='path/to/twilio',
    vol_min=20000
)


# Mocked loaded FCFTradeTracker.
MOCK_TARGET_TRACKER = FCFTargetTracker()


# Mocked loaded TradeChunker.
MOCK_TRADE_CHUNKER = TradeChunker(max_trade_size=1)


# Mocked loaded Strategy State.
MOCK_STARTING_STRATEGY_STATE = FCFStrategyState(
    has_started=False,
    h_to_e1_max=0.01,
    h_to_e2_max=0.02
)
MOCK_STARTING_STRATEGY_STATE.momentum = Momentum.NEUTRAL
MOCK_STARTING_STRATEGY_STATE.e1_targets = [
    (Decimal('1'), Decimal('2')),
    (Decimal('3'), Decimal('4')),
    (Decimal('5'), Decimal('6'))
]
MOCK_STARTING_STRATEGY_STATE.e2_targets = [
    (Decimal('7'), Decimal('8')),
    (Decimal('9'), Decimal('10')),
    (Decimal('11'), Decimal('12'))
]
MOCK_STARTING_STRATEGY_STATE.target_tracker = MOCK_TARGET_TRACKER
MOCK_STARTING_STRATEGY_STATE.trade_chunker = MOCK_TRADE_CHUNKER


# Mocked loaded Checkpoint.
MOCK_LOADED_CHECKPOINT=FCFCheckpoint(
    config=MOCK_STARTING_CONFIG,
    strategy_state=MOCK_STARTING_STRATEGY_STATE)


class TestResumeFabrictor:
    def _setup_mocks(self, mocker, in_yaml):
        mocker.patch.object(
            sys,
            'argv',
            [
                None,
                in_yaml,
                'some/db/path',
                'some-resume-id'
            ])
        mocker.patch.object(rf, '_connect_db')
        mocker.patch.object(getpass, 'getpass')
        mocker.patch.object(rf.db_handler, 'start_db')
        mocker.patch.object(
            rf, '_load_checkpoint', return_value=MOCK_LOADED_CHECKPOINT)
        mocker.patch.object(rf, 'input', return_value='y')
        mocker.patch.object(rf, '_export_config')
        mocker.patch.object(rf, '_export_checkpoint')

    def _validate_config(self, parsed_yaml):
        copy_mocked_config = copy.copy(MOCK_STARTING_CONFIG)
        for key, value in parsed_yaml['config_map'].items():
            if value is not None:
                assert getattr(MOCK_LOADED_CHECKPOINT.config, key) == value
            else:
                assert getattr(MOCK_LOADED_CHECKPOINT.config, key) == getattr(
                    copy_mocked_config, key)

    def _validate_strategy_state(self, parsed_yaml):
        copy_mocked_ss = copy.copy(MOCK_STARTING_STRATEGY_STATE)

        # Validate trivial strategy state attributes.
        strategy_state = MOCK_LOADED_CHECKPOINT.strategy_state
        for key, value in parsed_yaml['strategy_state_map'].items():
            if value is not None:
                assert getattr(strategy_state, key) == value
            else:
                assert getattr(strategy_state, key) == getattr(copy_mocked_ss, key)
        assert type(strategy_state.momentum) is Momentum
        assert type(strategy_state.has_started) is bool
        assert type(strategy_state.h_to_e1_max) is Decimal
        assert type(strategy_state.h_to_e2_max) is Decimal

        # Validate targets.
        # e1_targets.
        e1_targets = MOCK_LOADED_CHECKPOINT.strategy_state.e1_targets
        if parsed_yaml['e1_targets']:
            assert (e1_targets == parsed_yaml['e1_targets'])
        else:
            assert (e1_targets == copy_mocked_ss)

        for target in e1_targets:
            assert type(target) is tuple
            for price, vol in target:
                assert type(price) is Decimal
                assert type(vol) is Decimal

        # e2_targets.
        e2_targets = MOCK_LOADED_CHECKPOINT.strategy_state.e2_targets
        if parsed_yaml['e2_targets']:
            assert (e2_targets == parsed_yaml['e2_targets'])
        else:
            assert (e2_targets == copy_mocked_ss)

        for target in e2_targets:
            assert type(target) is tuple
            for price, vol in target:
                assert type(price) is Decimal
                assert type(vol) is Decimal

        # Validate Target Tracker.
        target_tracker = MOCK_LOADED_CHECKPOINT.strategy_state.target_tracker
        for key, value in parsed_yaml['target_tracker_map'].items():
            if value is not None:
                assert getattr(target_tracker, key) == value
            else:
                assert getattr(target_tracker, key) == getattr(copy_mocked_ss, key)
        assert type(target_tracker) is FCFTargetTracker
        assert type(target_tracker._target_index) is int
        assert type(target_tracker._last_target_index) is int

        # Validate Trade Chunker.
        trade_chunker = MOCK_LOADED_CHECKPOINT.strategy_state.trade_chunker
        for key, value in parsed_yaml['trade_chunker_map'].items():
            if value is not None:
                assert getattr(trade_chunker, key) == value
            else:
                assert getattr(trade_chunker, key) == getattr(copy_mocked_ss, key)
        assert type(trade_chunker) is FCFTargetTracker
        assert type(trade_chunker._max_trade_size) is Decimal
        assert type(trade_chunker._target) is Decimal
        assert type(trade_chunker._current_trade_size) is Decimal
        assert type(trade_chunker.trade_completed) is bool



    @pytest.mark.parametrize('in_yaml', [
        CURR_DIR + '/rf_partial.yaml',
        CURR_DIR + '/rf_full.yaml'
    ])
    def test_main_config_only(self, mocker, in_yaml):
        # Parse the input file.
        with open(in_yaml) as in_file:
            parsed_yaml = yaml.safe_load(in_file)

        self._setup_mocks(mocker, in_yaml)
        mocker.patch.object(rf, '_replace_strategy_state')

        rf.main()

        self._validate_config(parsed_yaml)

    def test_main_empty(self, mocker):
        in_yaml = CURR_DIR + '/rf_empty.yaml'

        self._setup_mocks(mocker, in_yaml)
        mocker.patch.object(rf, '_replace_strategy_state')

        with pytest.raises(SystemExit):
            rf.main()

    @pytest.mark.parametrize('in_yaml', [
        CURR_DIR + '/rf_partial.yaml',
        CURR_DIR + '/rf_full.yaml',
    ])
    def test_main_comprehensive(self, mocker, in_yaml):
        # Parse the input file.
        with open(in_yaml) as in_file:
            parsed_yaml = yaml.safe_load(in_file)

        self._setup_mocks(mocker, in_yaml)

        rf.main()

        self._validate_config(parsed_yaml)
