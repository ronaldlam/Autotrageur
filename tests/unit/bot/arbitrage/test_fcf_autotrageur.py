# pylint: disable=E1101
import builtins
import copy
import copyreg
import getpass
import os
import pickle
import time
import traceback
import uuid
from decimal import Decimal
from unittest.mock import Mock

import ccxt
import pytest
import schedule
import yaml
from ccxt import ExchangeError

import autotrageur.bot.arbitrage.arbseeker as arbseeker
import autotrageur.bot.arbitrage.fcf_autotrageur
import fp_libs.db.maria_db_handler as db_handler
from autotrageur.bot.arbitrage.arbseeker import SpreadOpportunity
from autotrageur.bot.arbitrage.fcf.fcf_stat_tracker import FCFStatTracker
from autotrageur.bot.arbitrage.fcf.strategy import TradeMetadata
from autotrageur.bot.arbitrage.fcf_autotrageur import (DEFAULT_PHONE_MESSAGE,
                                                       AutotrageurAuthenticationError,
                                                       FCFAlertError,
                                                       FCFAutotrageur,
                                                       FCFCheckpoint,
                                                       IncompleteArbitrageError,
                                                       IncorrectStateObjectTypeError,
                                                       arbseeker)
from autotrageur.bot.common.config_constants import (TWILIO_RECIPIENT_NUMBERS,
                                                     TWILIO_SENDER_NUMBER)
from autotrageur.bot.common.db_constants import (FCF_AUTOTRAGEUR_CONFIG_COLUMNS,
                                                 FCF_AUTOTRAGEUR_CONFIG_PRIM_KEY_ID,
                                                 FCF_AUTOTRAGEUR_CONFIG_PRIM_KEY_START_TS,
                                                 FCF_AUTOTRAGEUR_CONFIG_TABLE,
                                                 FCF_MEASURES_PRIM_KEY_ID,
                                                 FCF_MEASURES_TABLE,
                                                 FCF_STATE_PRIM_KEY_ID,
                                                 FCF_STATE_TABLE,
                                                 FOREX_RATE_PRIM_KEY_ID,
                                                 FOREX_RATE_TABLE,
                                                 TRADE_OPPORTUNITY_PRIM_KEY_ID,
                                                 TRADE_OPPORTUNITY_TABLE,
                                                 TRADES_PRIM_KEY_SIDE,
                                                 TRADES_PRIM_KEY_TRADE_OPP_ID,
                                                 TRADES_TABLE)
from autotrageur.bot.common.notification_constants import SUBJECT_LIVE_FAILURE
from autotrageur.bot.trader.dry_run import DryRunExchange
from fp_libs.constants.ccxt_constants import API_KEY, API_SECRET, PASSWORD
from fp_libs.db.maria_db_handler import InsertRowObject
from fp_libs.utilities import num_to_decimal

xfail = pytest.mark.xfail


# Test constants.
FAKE_BUY_PRICE = num_to_decimal(100.99)
FAKE_SELL_PRICE = num_to_decimal(105.99)
FAKE_PRE_FEE_BASE = num_to_decimal(10.00)
FAKE_PRE_FEE_QUOTE_BUY = FAKE_BUY_PRICE
FAKE_PRE_FEE_QUOTE_SELL = FAKE_SELL_PRICE

FAKE_POST_FEE_BASE = num_to_decimal(10.00)
FAKE_POST_FEE_QUOTE_BUY = FAKE_BUY_PRICE
FAKE_POST_FEE_QUOTE_SELL = FAKE_SELL_PRICE

FAKE_UNIFIED_RESPONSE_BUY = {
    'pre_fee_base': FAKE_PRE_FEE_BASE,
    'pre_fee_quote': FAKE_PRE_FEE_QUOTE_BUY,
    'post_fee_base': FAKE_POST_FEE_BASE,
    'post_fee_quote': FAKE_POST_FEE_QUOTE_BUY
}

FAKE_UNIFIED_RESPONSE_SELL = {
    'pre_fee_base': FAKE_PRE_FEE_BASE,
    'pre_fee_quote': FAKE_PRE_FEE_QUOTE_SELL,
    'post_fee_base': FAKE_POST_FEE_BASE,
    'post_fee_quote': FAKE_POST_FEE_QUOTE_SELL
}

FAKE_UNIFIED_RESPONSE_DIFFERENT_AMOUNT = {
    'pre_fee_base': num_to_decimal(101.99),
    'pre_fee_quote': FAKE_PRE_FEE_QUOTE_SELL,
    'post_fee_base': FAKE_POST_FEE_BASE,
    'post_fee_quote': FAKE_POST_FEE_QUOTE_SELL
}

FAKE_CONFIG_UUID = str(uuid.uuid4())
FAKE_RESUME_UUID = str(uuid.uuid4())
FAKE_NEW_STATE_UUID = str(uuid.uuid4())
FAKE_NEW_STAT_TRACKER_UUID = str(uuid.uuid4())
FAKE_SPREAD_OPP_ID = 9999
FAKE_CURR_TIME = time.time()
FAKE_CONFIG_ROW = { 'fake': 'config_row' }
FAKE_STRATEGY_STATE_RESTORED = Mock()


@pytest.fixture(scope='module')
def no_patch_fcf_autotrageur():
    fcf_instance = FCFAutotrageur()
    fcf_instance._config = Mock()
    return fcf_instance


@pytest.fixture()
def fcf_autotrageur(mocker, fake_ccxt_trader):
    f = FCFAutotrageur()
    f.config = {
        'email_cfg_path': 'fake/path/to/config.yaml',
        'spread_target_low': 1.0,
        'spread_target_high': 5.0
    }
    f.trade_metadata = TradeMetadata(None, None, None, None, None)
    trader1 = fake_ccxt_trader
    trader2 = copy.deepcopy(fake_ccxt_trader)
    mocker.patch.object(f, 'trader1', trader1, create=True)
    mocker.patch.object(f, 'trader2', trader2, create=True)
    return f


@pytest.fixture()
def fcf_checkpoint(mocker):
    return FCFCheckpoint(FAKE_CONFIG_UUID)


def test_load_twilio(mocker, no_patch_fcf_autotrageur):
    FAKE_TWILIO_CFG_PATH = 'fake/twilio/cfg/path'
    fake_open = mocker.patch('builtins.open', mocker.mock_open())
    fake_yaml_safe_load = mocker.patch.object(yaml, 'safe_load')
    fake_twilio_client = mocker.Mock()
    fake_twilio_client_constructor = mocker.patch.object(
        autotrageur.bot.arbitrage.fcf_autotrageur, 'TwilioClient', return_value=fake_twilio_client)
    fake_test_connection = mocker.patch.object(fake_twilio_client, 'test_connection')
    mocker.patch('os.getenv', return_value='some_env_var')
    mocker.patch.object(no_patch_fcf_autotrageur, 'logger', mocker.Mock(), create=True)

    no_patch_fcf_autotrageur._FCFAutotrageur__load_twilio(FAKE_TWILIO_CFG_PATH)

    fake_open.assert_called_once_with(FAKE_TWILIO_CFG_PATH, 'r')
    fake_yaml_safe_load.assert_called_once()
    fake_twilio_client_constructor.assert_called_once_with(
        os.getenv('ACCOUNT_SID'), os.getenv('AUTH_TOKEN'),
        no_patch_fcf_autotrageur.logger)
    fake_test_connection.assert_called_once_with()


@pytest.mark.parametrize(
    "decrypt_success, dryrun", [
        (True, True),
        (True, False),
        (False, True),
        pytest.param(False, False,
            marks=pytest.mark.xfail(strict=True, raises=IOError)),
    ]
)
def test_parse_keyfile(mocker, no_patch_fcf_autotrageur, decrypt_success, dryrun):
    args = mocker.MagicMock()
    mocker.patch('getpass.getpass')
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'dryrun', dryrun)
    mock_decrypt = mocker.patch.object(autotrageur.bot.arbitrage.fcf_autotrageur, 'decrypt')
    mock_kf_to_map = mocker.patch.object(autotrageur.bot.arbitrage.fcf_autotrageur, 'keyfile_to_map')

    if not decrypt_success:
        mock_decrypt.side_effect = Exception

    key_map = no_patch_fcf_autotrageur._FCFAutotrageur__parse_keyfile(args)

    getpass.getpass.assert_called_once_with(prompt="Enter keyfile password:")   # pylint: disable=E1101
    if decrypt_success:
        mock_decrypt.assert_called_once()
        mock_kf_to_map.assert_called_once()
        assert(key_map)
    elif not dryrun:
        mock_decrypt.assert_called_once()
        mock_kf_to_map.assert_not_called()
        assert key_map is None
    else:
        mock_decrypt.assert_called_once()
        mock_kf_to_map.assert_not_called()
        assert not (key_map)


def test_persist_config(mocker, no_patch_fcf_autotrageur):
    mocker.patch.object(db_handler, 'build_row', return_value=FAKE_CONFIG_ROW)
    mocker.patch.object(db_handler, 'insert_row')
    mocker.patch.object(db_handler, 'commit_all')

    no_patch_fcf_autotrageur._FCFAutotrageur__persist_config()

    db_handler.build_row.assert_called_once_with(
        FCF_AUTOTRAGEUR_CONFIG_COLUMNS, no_patch_fcf_autotrageur._config._asdict())
    db_handler.insert_row.assert_called_once_with(
        InsertRowObject(
            FCF_AUTOTRAGEUR_CONFIG_TABLE,
            FAKE_CONFIG_ROW,
            (FCF_AUTOTRAGEUR_CONFIG_PRIM_KEY_ID,
            FCF_AUTOTRAGEUR_CONFIG_PRIM_KEY_START_TS)))
    db_handler.commit_all.assert_called_once_with()


def test_persist_forex(mocker, no_patch_fcf_autotrageur):
    mocker.patch.object(time, 'time', return_value=FAKE_CURR_TIME)
    mocker.patch.object(uuid, 'uuid4', return_value=FAKE_CONFIG_UUID)
    mocker.patch.object(db_handler, 'insert_row')
    mocker.patch.object(db_handler, 'commit_all')
    mock_trader = mocker.Mock()
    mock_trader.quote = 'SOME_QUOTE'
    mock_trader.forex_ratio = Decimal('195766')

    no_patch_fcf_autotrageur._FCFAutotrageur__persist_forex(mock_trader)

    ROW_DATA = {
        'id': str(FAKE_CONFIG_UUID),
        'quote': mock_trader.quote,
        'rate': mock_trader.forex_ratio,
        'local_timestamp': int(FAKE_CURR_TIME)
    }
    forex_row_obj = InsertRowObject(
        FOREX_RATE_TABLE, ROW_DATA, (FOREX_RATE_PRIM_KEY_ID,))
    db_handler.insert_row.assert_called_once_with(forex_row_obj)
    db_handler.commit_all.assert_called_once_with()


def test_update_forex(mocker, no_patch_fcf_autotrageur):
    persist_forex = mocker.patch.object(
        no_patch_fcf_autotrageur, '_FCFAutotrageur__persist_forex')
    mock_trader = mocker.Mock()

    no_patch_fcf_autotrageur._FCFAutotrageur__update_forex(mock_trader)

    mock_trader.set_forex_ratio.assert_called_once_with()
    persist_forex.assert_called_once_with(mock_trader)


@pytest.mark.parametrize('buy_response', [
    None, FAKE_UNIFIED_RESPONSE_BUY
])
@pytest.mark.parametrize('sell_response', [
    None, FAKE_UNIFIED_RESPONSE_SELL
])
def test_persist_trade_data(mocker, no_patch_fcf_autotrageur,
                            buy_response, sell_response):
    # Copy the response dicts, as the tested function mutates the variables.
    buy_response_copy = copy.deepcopy(buy_response)
    sell_response_copy = copy.deepcopy(sell_response)

    trade_metadata = TradeMetadata(
        SpreadOpportunity(
            FAKE_SPREAD_OPP_ID, None, None, None, None, None, None, None, None),
        None, None, None, None)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'id', FAKE_CONFIG_UUID)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'start_timestamp', FAKE_CURR_TIME)
    mocker.patch.object(db_handler, 'insert_row')
    mocker.patch.object(db_handler, 'commit_all')

    # Number of insert calls will vary depending on number of successful trades.
    insert_num_calls = 1
    insert_call_args_list = [
        mocker.call(
            InsertRowObject(
                TRADE_OPPORTUNITY_TABLE,
                trade_metadata.spread_opp._asdict(),
                (TRADE_OPPORTUNITY_PRIM_KEY_ID, )))
    ]

    # Check that the ids are not populated until function is called.
    if buy_response_copy is not None:
        assert buy_response_copy.get('trade_opportunity_id') is None
        assert buy_response_copy.get('autotrageur_config_id') is None
        assert buy_response_copy.get('autotrageur_config_start_timestamp') is None
    if sell_response_copy is not None:
        assert sell_response_copy.get('trade_opportunity_id') is None
        assert sell_response_copy.get('autotrageur_config_id') is None
        assert sell_response_copy.get('autotrageur_config_start_timestamp') is None
    no_patch_fcf_autotrageur._FCFAutotrageur__persist_trade_data(
        buy_response_copy, sell_response_copy, trade_metadata)

    if buy_response_copy is not None:
        insert_num_calls += 1
        insert_call_args_list.append(mocker.call(
            InsertRowObject(
                TRADES_TABLE,
                buy_response_copy,
                (TRADES_PRIM_KEY_TRADE_OPP_ID, TRADES_PRIM_KEY_SIDE))
        ))
        assert buy_response_copy.get('trade_opportunity_id') is FAKE_SPREAD_OPP_ID
        assert buy_response_copy.get('autotrageur_config_id') is FAKE_CONFIG_UUID
        assert buy_response_copy.get('autotrageur_config_start_timestamp') is FAKE_CURR_TIME

    if sell_response_copy is not None:
        insert_num_calls += 1
        insert_call_args_list.append(mocker.call(
            InsertRowObject(
                TRADES_TABLE,
                sell_response_copy,
                (TRADES_PRIM_KEY_TRADE_OPP_ID, TRADES_PRIM_KEY_SIDE))
        ))
        assert sell_response_copy.get('trade_opportunity_id') is FAKE_SPREAD_OPP_ID
        assert sell_response_copy.get('autotrageur_config_id') is FAKE_CONFIG_UUID
        assert sell_response_copy.get('autotrageur_config_start_timestamp') is FAKE_CURR_TIME

    assert db_handler.insert_row.call_count == insert_num_calls
    assert db_handler.insert_row.call_args_list == insert_call_args_list
    db_handler.commit_all.assert_called_once_with()


@pytest.mark.parametrize('resume_id', [None, 'abcdef'])
def test_setup_dry_run_exchanges(mocker, no_patch_fcf_autotrageur, resume_id):
    MOCK_E1 = 'Gemini'
    MOCK_E2 = 'Bithumb'
    MOCK_E1_PAIR = 'ETH/USD'
    MOCK_E2_PAIR = 'ETH/KRW'
    MOCK_E1_BASE_BAL = 5
    MOCK_E1_QUOTE_BAL = 2000
    MOCK_E2_BASE_BAL = 10
    MOCK_E2_QUOTE_BAL = 20000

    mocker.patch.object(no_patch_fcf_autotrageur._config, 'exchange1', MOCK_E1)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'exchange2', MOCK_E2)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'exchange1_pair', MOCK_E1_PAIR)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'exchange2_pair', MOCK_E2_PAIR)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'dryrun_e1_base', MOCK_E1_BASE_BAL)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'dryrun_e1_quote', MOCK_E1_QUOTE_BAL)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'dryrun_e2_base', MOCK_E2_BASE_BAL)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'dryrun_e2_quote', MOCK_E2_QUOTE_BAL)
    mock_stat_tracker = mocker.patch.object(no_patch_fcf_autotrageur, '_stat_tracker', create=True)

    mock_dry_e1, mock_dry_e2 = no_patch_fcf_autotrageur._FCFAutotrageur__setup_dry_run_exchanges(resume_id)

    if resume_id:
        assert mock_dry_e1 is mock_stat_tracker.dry_run_e1
        assert mock_dry_e2 is mock_stat_tracker.dry_run_e2
    else:
        assert mock_dry_e1.name == MOCK_E1
        assert mock_dry_e1.base == 'ETH'
        assert mock_dry_e1.quote == 'USD'
        assert mock_dry_e1.base_balance == num_to_decimal(MOCK_E1_BASE_BAL)
        assert mock_dry_e1.quote_balance == num_to_decimal(MOCK_E1_QUOTE_BAL)
        assert mock_dry_e2.name == MOCK_E2
        assert mock_dry_e2.base == 'ETH'
        assert mock_dry_e2.quote == 'KRW'
        assert mock_dry_e2.base_balance == num_to_decimal(MOCK_E2_BASE_BAL)
        assert mock_dry_e2.quote_balance == num_to_decimal(MOCK_E2_QUOTE_BAL)


@pytest.mark.parametrize("client_quote_usd", [True, False])
def test_setup_forex(mocker, no_patch_fcf_autotrageur, client_quote_usd):
    trader1 = mocker.patch.object(no_patch_fcf_autotrageur, 'trader1',
        create=True)
    trader2 = mocker.patch.object(no_patch_fcf_autotrageur, 'trader2',
        create=True)
    mock_update_forex = mocker.patch.object(no_patch_fcf_autotrageur, '_FCFAutotrageur__update_forex')
    mocker.spy(schedule, 'every')

    if client_quote_usd:
        trader1.quote = 'USD'
        trader2.quote = 'USD'
        no_patch_fcf_autotrageur._FCFAutotrageur__setup_forex()
        assert(schedule.every.call_count == 0)          # pylint: disable=E1101
        assert len(schedule.jobs) == 0
        assert(mock_update_forex.call_count == 0)
    else:
        # Set a fiat quote pair that is not USD to trigger conversion calls.
        trader1.quote = 'KRW'
        trader2.quote = 'KRW'
        no_patch_fcf_autotrageur._FCFAutotrageur__setup_forex()
        assert trader1.conversion_needed is True
        assert trader2.conversion_needed is True
        assert(schedule.every.call_count == 2)          # pylint: disable=E1101
        assert len(schedule.jobs) == 2
        assert(mock_update_forex.call_count == 2)

    schedule.clear()


@pytest.mark.parametrize('resume_id', [None, 'abcdef'])
@pytest.mark.parametrize('use_test_api', [True, False])
@pytest.mark.parametrize('dryrun', [True, False])
def test_setup_stat_tracker(mocker, no_patch_fcf_autotrageur, resume_id, dryrun, use_test_api):
    FAKE_STAT_TRACKER = mocker.Mock()
    FAKE_TRADER1 = mocker.Mock()
    FAKE_TRADER2 = mocker.Mock()
    mocker.patch.object(uuid, 'uuid4', return_value=FAKE_NEW_STAT_TRACKER_UUID)
    mock_fancy_log = mocker.patch.object(autotrageur.bot.arbitrage.fcf_autotrageur, 'fancy_log')
    mock_stat_tracker_constructor = mocker.patch.object(
        autotrageur.bot.arbitrage.fcf_autotrageur,
        'FCFStatTracker',
        return_value=FAKE_STAT_TRACKER)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'dryrun', dryrun)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'use_test_api', use_test_api)
    mocker.patch.object(no_patch_fcf_autotrageur, 'trader1', FAKE_TRADER1, create=True)
    mocker.patch.object(no_patch_fcf_autotrageur, 'trader2', FAKE_TRADER2, create=True)
    mock_insert_row = mocker.patch.object(db_handler, 'insert_row')
    mock_commit_all = mocker.patch.object(db_handler, 'commit_all')
    MOCK_FCF_MEASURES_ROW_DATA = {
        'id': FAKE_NEW_STAT_TRACKER_UUID,
        'autotrageur_config_id': no_patch_fcf_autotrageur._config.id,
        'autotrageur_config_start_timestamp': no_patch_fcf_autotrageur._config.start_timestamp,
        'autotrageur_stop_timestamp': None,
        'e1_start_bal_base': no_patch_fcf_autotrageur.trader1.base_bal,
        'e1_close_bal_base': no_patch_fcf_autotrageur.trader1.base_bal,
        'e2_start_bal_base': no_patch_fcf_autotrageur.trader2.base_bal,
        'e2_close_bal_base': no_patch_fcf_autotrageur.trader2.base_bal,
        'e1_start_bal_quote': no_patch_fcf_autotrageur.trader1.quote_bal,
        'e1_close_bal_quote': no_patch_fcf_autotrageur.trader1.quote_bal,
        'e2_start_bal_quote': no_patch_fcf_autotrageur.trader2.quote_bal,
        'e2_close_bal_quote': no_patch_fcf_autotrageur.trader2.quote_bal,
        'num_fatal_errors': 0,
        'trade_count': 0
    }

    no_patch_fcf_autotrageur._FCFAutotrageur__setup_stat_tracker(resume_id)

    fancy_log_call_args_list = []
    if resume_id:
        if use_test_api:
            fancy_log_call_args_list.append(mocker.call(
                "Resumed bot running against TEST Exchange APIs."))
        else:
            fancy_log_call_args_list.append(mocker.call(
                "Resumed bot running against LIVE Exchange APIs."))

        if dryrun:
            fancy_log_call_args_list.append(mocker.call(
                "Resumed - DRY RUN mode. Trades will NOT execute on actual "
                "exchanges."))
    else:
        if dryrun:
            fancy_log_call_args_list.append(mocker.call(
                "DRY RUN mode initiated. Trades will NOT execute on actual"
                " exchanges."))
        else:
            mock_fancy_log.assert_not_called()

        assert mock_fancy_log.call_args_list == fancy_log_call_args_list
        mock_stat_tracker_constructor.assert_called_once_with(
            new_id=FAKE_NEW_STAT_TRACKER_UUID,
            e1_trader=FAKE_TRADER1,
            e2_trader=FAKE_TRADER2)
        assert no_patch_fcf_autotrageur._stat_tracker == FAKE_STAT_TRACKER
        mock_insert_row.assert_called_once_with(
            InsertRowObject(
                FCF_MEASURES_TABLE,
                MOCK_FCF_MEASURES_ROW_DATA,
                (FCF_MEASURES_PRIM_KEY_ID,)))
        mock_commit_all.assert_called_once_with()


@pytest.mark.parametrize('exc_type', [ccxt.AuthenticationError, ccxt.ExchangeNotAvailable])
@pytest.mark.parametrize('balance_check_success', [True, False])
@pytest.mark.parametrize('use_test_api', [True, False])
@pytest.mark.parametrize('dryrun', [True, False])
def test_setup_traders(mocker, no_patch_fcf_autotrageur, dryrun, use_test_api,
                       balance_check_success, exc_type):
    fake_slippage = 0.25
    fake_pair = 'fake/pair'
    fake_exchange_key_map = {
        'fake': {
            API_KEY: 'API_KEY',
            API_SECRET: 'API_SECRET',
            PASSWORD: 'PASSWORD'
        },
        'pair': {
            API_KEY: 'API_KEY',
            API_SECRET: 'API_SECRET',
            PASSWORD: 'PASSWORD'
        }
    }
    placeholder = 'fake'
    mock_trader1 = mocker.Mock()
    mock_trader2 = mocker.Mock()
    mock_ccxt_trader_constructor = mocker.patch('autotrageur.bot.arbitrage.fcf_autotrageur.CCXTTrader')
    mock_ccxt_trader_constructor.side_effect = [mock_trader1, mock_trader2]
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'exchange1_pair', fake_pair)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'exchange2_pair', fake_pair)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'exchange1', placeholder)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'exchange2', placeholder)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'slippage', fake_slippage)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'use_test_api', use_test_api)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'dryrun', dryrun)
    mock_setup_dr_exchanges = mocker.patch.object(
        no_patch_fcf_autotrageur, '_FCFAutotrageur__setup_dry_run_exchanges')
    if dryrun:
        mock_setup_dr_exchanges.return_value = mocker.Mock(), mocker.Mock()

    # If wallet balance fetch fails, expect either ccxt.AuthenticationError or
    # ccxt.ExchangeNotAvailable to be raised.
    if balance_check_success is False:
        # For testing purposes, only need one trader to throw an exception.
        mock_trader1.update_wallet_balances.side_effect = exc_type
        with pytest.raises(AutotrageurAuthenticationError):
            no_patch_fcf_autotrageur._FCFAutotrageur__setup_traders(fake_exchange_key_map, None)

        # Expect called once and encountered exception.
        mock_trader1.update_wallet_balances.assert_called_once_with()
        mock_trader2.update_wallet_balances.assert_not_called()
    else:
        no_patch_fcf_autotrageur._FCFAutotrageur__setup_traders(fake_exchange_key_map, None)
        mock_trader1.update_wallet_balances.assert_called_once_with()
        mock_trader2.update_wallet_balances.assert_called_once_with()
        assert(mock_trader1.load_markets.call_count == 1)
        assert(mock_trader2.load_markets.call_count == 1)

    if dryrun:
        assert mock_setup_dr_exchanges.call_count == 1
    else:
        assert mock_setup_dr_exchanges.call_count == 0

    if use_test_api:
        assert(mock_trader1.connect_test_api.call_count == 1)
        assert(mock_trader2.connect_test_api.call_count == 1)
    else:
        assert(mock_trader1.connect_test_api.call_count == 0)
        assert(mock_trader2.connect_test_api.call_count == 0)


class TestVerifySoldAmount:
    @pytest.mark.parametrize('rounded_sell_amount, amount_precision, sold_base', [
        (Decimal('1.24'), 2, Decimal('1.24')),
        (Decimal('1.24'), 2, Decimal('1.23')),
        (Decimal('1.24'), 2, Decimal('1.25')),
        (Decimal('1.2415235242'), 10, Decimal('1.2415235242')),
        (Decimal('1.2415235241'), 10, Decimal('1.2415235242')),
        (Decimal('1.2415235243'), 10, Decimal('1.2415235242')),
        (Decimal('1.241523524312'), None, Decimal('1.241523524312')),
    ])
    def test_verify_sold_amount(self, mocker, no_patch_fcf_autotrageur,
                                rounded_sell_amount, amount_precision,
                                sold_base):
        bought_amount = mocker.Mock()
        sell_trader = mocker.Mock()
        buy_response = mocker.Mock()
        sell_response = {'pre_fee_base': sold_base}

        sell_trader.round_exchange_precision.return_value = rounded_sell_amount
        sell_trader.get_amount_precision.return_value = amount_precision

        no_patch_fcf_autotrageur._FCFAutotrageur__verify_sold_amount(
            bought_amount, sell_trader, buy_response, sell_response)

    @pytest.mark.parametrize('rounded_sell_amount, amount_precision, sold_base', [
        (Decimal('1.23'), 2, Decimal('1.25')),
        (Decimal('1.26'), 2, Decimal('1.23')),
        (Decimal('2.24'), 2, Decimal('1.25')),
        (Decimal('1.2415235242'), 10, Decimal('1.2415235244')),
        (Decimal('1.2415235242'), 10, Decimal('1.2415235240')),
        (Decimal('1.2415235242'), 10, Decimal('1.2416235242')),
        (Decimal('1.241523524312'), None, Decimal('1.241523524311')),
        (Decimal('1.241523524312'), None, Decimal('1.241523524313')),
    ])
    def test_verify_sold_amount_err(self, mocker, no_patch_fcf_autotrageur,
                                    rounded_sell_amount, amount_precision,
                                    sold_base):
        bought_amount = mocker.Mock()
        sell_trader = mocker.Mock()
        buy_response = mocker.Mock()
        sell_response = {'pre_fee_base': sold_base}

        sell_trader.round_exchange_precision.return_value = rounded_sell_amount
        sell_trader.get_amount_precision.return_value = amount_precision

        with pytest.raises(IncompleteArbitrageError):
            no_patch_fcf_autotrageur._FCFAutotrageur__verify_sold_amount(
                bought_amount, sell_trader, buy_response, sell_response)


def test_construct_strategy(mocker, no_patch_fcf_autotrageur):
    SPREAD_MIN = 1.3
    VOL_MIN = 1000
    H_TO_E1_MAX = 3
    H_TO_E2_MAX = 50
    MAX_TRADE_SIZE = 200
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'h_to_e1_max', H_TO_E1_MAX)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'h_to_e2_max', H_TO_E2_MAX)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'max_trade_size', MAX_TRADE_SIZE)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'spread_min', SPREAD_MIN)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'vol_min', VOL_MIN)

    mock_strategy = mocker.Mock()
    mock_strategy_builder = mocker.Mock()
    mock_strategy_builder.build.return_value = mock_strategy
    mock_strategy_builder_constructor = mocker.patch(
        'autotrageur.bot.arbitrage.fcf_autotrageur.FCFStrategyBuilder',
        return_value=mock_strategy_builder)

    mock_strategy_builder.set_has_started.return_value = mock_strategy_builder
    mock_strategy_builder.set_h_to_e1_max.return_value = mock_strategy_builder
    mock_strategy_builder.set_h_to_e2_max.return_value = mock_strategy_builder
    mock_strategy_builder.set_max_trade_size.return_value = mock_strategy_builder
    mock_strategy_builder.set_spread_min.return_value = mock_strategy_builder
    mock_strategy_builder.set_vol_min.return_value = mock_strategy_builder
    mock_strategy_builder.set_manager.return_value = mock_strategy_builder

    no_patch_fcf_autotrageur._FCFAutotrageur__construct_strategy()

    mock_strategy_builder_constructor.assert_called_once_with()
    mock_strategy_builder.set_has_started.assert_called_once_with(False)
    mock_strategy_builder.set_h_to_e1_max.assert_called_once_with(Decimal('3'))
    mock_strategy_builder.set_h_to_e2_max.assert_called_once_with(Decimal('50'))
    mock_strategy_builder.set_max_trade_size.assert_called_once_with(Decimal('200'))
    mock_strategy_builder.set_spread_min.assert_called_once_with(Decimal('1.3'))
    mock_strategy_builder.set_vol_min.assert_called_once_with(Decimal('1000'))
    mock_strategy_builder.set_manager.assert_called_once_with(no_patch_fcf_autotrageur)
    mock_strategy_builder.build.assert_called_once_with()


class TestExecuteTrade:
    def _setup_mocks(
            self, mocker, fake_ccxt_trader, no_patch_fcf_autotrageur, dryrun):
        trader1 = fake_ccxt_trader
        trader2 = copy.deepcopy(fake_ccxt_trader)
        mocker.patch.object(no_patch_fcf_autotrageur, 'trader1', trader1, create=True)
        mocker.patch.object(no_patch_fcf_autotrageur, 'trader2', trader2, create=True)
        mocker.patch.object(
            no_patch_fcf_autotrageur._config, 'dryrun', dryrun)
        mocker.patch.object(no_patch_fcf_autotrageur, '_strategy', create=True)
        mocker.patch.object(no_patch_fcf_autotrageur, 'checkpoint', create=True)
        mocker.patch.object(
            no_patch_fcf_autotrageur.checkpoint, 'strategy_state', FAKE_STRATEGY_STATE_RESTORED)
        mocker.patch.object(no_patch_fcf_autotrageur._strategy, 'get_trade_data',
            return_value=TradeMetadata(
                spread_opp=None,
                buy_price=FAKE_BUY_PRICE,
                sell_price=FAKE_SELL_PRICE,
                buy_trader=no_patch_fcf_autotrageur.trader1,
                sell_trader=no_patch_fcf_autotrageur.trader2
            ), create=True)
        mocker.patch.object(
            arbseeker, 'execute_buy', return_value=FAKE_UNIFIED_RESPONSE_BUY)
        mocker.patch.object(
            arbseeker, 'execute_sell', return_value=FAKE_UNIFIED_RESPONSE_SELL)
        mocker.patch.object(
            no_patch_fcf_autotrageur, '_FCFAutotrageur__persist_trade_data', create=True)
        mocker.patch.object(no_patch_fcf_autotrageur, '_send_email')
        mocker.patch.object(no_patch_fcf_autotrageur, '_stat_tracker', create=True)
        mocker.patch.object(no_patch_fcf_autotrageur._stat_tracker, 'trade_count', 0)
        if dryrun:
            mocker.patch.object(no_patch_fcf_autotrageur._stat_tracker, 'log_balances', create=True)

    @pytest.mark.parametrize('dryrun', [True, False])
    def test_execute_trade(self, mocker, fake_ccxt_trader,
                           no_patch_fcf_autotrageur, dryrun):
        self._setup_mocks(mocker, fake_ccxt_trader,
            no_patch_fcf_autotrageur, dryrun)

        no_patch_fcf_autotrageur._execute_trade()

        trade_metadata = no_patch_fcf_autotrageur._strategy.get_trade_data.return_value
        arbseeker.execute_buy.assert_called_once_with(
            trade_metadata.buy_trader,
            trade_metadata.buy_price)
        arbseeker.execute_sell.assert_called_once_with(
            trade_metadata.sell_trader,
            trade_metadata.sell_price,
            FAKE_UNIFIED_RESPONSE_BUY['post_fee_base'])
        no_patch_fcf_autotrageur._FCFAutotrageur__persist_trade_data.assert_called_once_with(
            FAKE_UNIFIED_RESPONSE_BUY, FAKE_UNIFIED_RESPONSE_SELL, trade_metadata)
        no_patch_fcf_autotrageur._strategy.finalize_trade.assert_called_once_with(
            FAKE_UNIFIED_RESPONSE_BUY, FAKE_UNIFIED_RESPONSE_SELL)

        if dryrun:
            no_patch_fcf_autotrageur._stat_tracker.log_balances.assert_called_once_with()
            no_patch_fcf_autotrageur._send_email.assert_not_called()
        else:
            no_patch_fcf_autotrageur._send_email.assert_called_once()
        assert no_patch_fcf_autotrageur._stat_tracker.trade_count == 2

    @pytest.mark.parametrize('exc_type', [
        ExchangeError,
        Exception
    ])
    def test_execute_trade_buy_exchange_err(self, mocker, fake_ccxt_trader,
                                            no_patch_fcf_autotrageur, exc_type):
        self._setup_mocks(mocker, fake_ccxt_trader,
                          no_patch_fcf_autotrageur, False)
        arbseeker.execute_buy.side_effect = exc_type

        no_patch_fcf_autotrageur._execute_trade()

        trade_metadata = no_patch_fcf_autotrageur._strategy.get_trade_data.return_value
        mock_persist_data = no_patch_fcf_autotrageur._FCFAutotrageur__persist_trade_data
        arbseeker.execute_buy.assert_called_once_with(
            trade_metadata.buy_trader,
            trade_metadata.buy_price)
        arbseeker.execute_sell.assert_not_called()
        mock_persist_data.assert_called_once_with(None, None, trade_metadata)
        assert no_patch_fcf_autotrageur._strategy.strategy_state is FAKE_STRATEGY_STATE_RESTORED
        no_patch_fcf_autotrageur._strategy.finalize_trade.assert_not_called()
        no_patch_fcf_autotrageur._send_email.assert_called_once()
        assert no_patch_fcf_autotrageur._stat_tracker.trade_count == 0

    @pytest.mark.parametrize('exc_type', [
        ExchangeError,
        Exception,
        IncompleteArbitrageError
    ])
    def test_execute_trade_sell_error(self, mocker, fake_ccxt_trader,
                                      no_patch_fcf_autotrageur, exc_type):
        self._setup_mocks(mocker, fake_ccxt_trader,
                          no_patch_fcf_autotrageur, False)

        if exc_type is IncompleteArbitrageError:
            arbseeker.execute_sell.return_value = FAKE_UNIFIED_RESPONSE_DIFFERENT_AMOUNT
        else:
            arbseeker.execute_sell.side_effect = exc_type

        with pytest.raises(exc_type):
            no_patch_fcf_autotrageur._execute_trade()

        trade_metadata = no_patch_fcf_autotrageur._strategy.get_trade_data.return_value
        mock_persist_data = no_patch_fcf_autotrageur._FCFAutotrageur__persist_trade_data
        arbseeker.execute_buy.assert_called_once_with(
            trade_metadata.buy_trader,
            trade_metadata.buy_price)
        arbseeker.execute_sell.assert_called_once_with(
            trade_metadata.sell_trader,
            trade_metadata.sell_price,
            FAKE_UNIFIED_RESPONSE_BUY['post_fee_base'])

        # IncompleteArbitrageError gets raised with a populated sell_response,
        # just that the base amount doesn't match the buy_order.
        if exc_type is IncompleteArbitrageError:
            mock_persist_data.assert_called_once_with(
                FAKE_UNIFIED_RESPONSE_BUY,
                FAKE_UNIFIED_RESPONSE_DIFFERENT_AMOUNT,
                trade_metadata)
        else:
            mock_persist_data.assert_called_once_with(
                FAKE_UNIFIED_RESPONSE_BUY, None, trade_metadata)
        no_patch_fcf_autotrageur._strategy.restore.assert_not_called()
        no_patch_fcf_autotrageur._strategy.finalize_trade.assert_not_called()
        no_patch_fcf_autotrageur._send_email.assert_called_once()
        assert no_patch_fcf_autotrageur._stat_tracker.trade_count == 1


def test_clean_up(mocker, no_patch_fcf_autotrageur):
    mock_strategy = mocker.patch.object(
        no_patch_fcf_autotrageur, '_strategy', create=True)

    no_patch_fcf_autotrageur._clean_up()

    mock_strategy.clean_up.assert_called_once_with()


def test_export_state(mocker, no_patch_fcf_autotrageur, fcf_checkpoint):
    mocker.patch.object(no_patch_fcf_autotrageur, 'trader1', create=True)
    mocker.patch.object(no_patch_fcf_autotrageur, 'trader2', create=True)
    FAKE_STAT_TRACKER = FCFStatTracker(
        None, no_patch_fcf_autotrageur.trader1, no_patch_fcf_autotrageur.trader2)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'id', FAKE_CONFIG_UUID)
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'start_timestamp', FAKE_CURR_TIME)
    mocker.patch.object(no_patch_fcf_autotrageur, 'checkpoint', fcf_checkpoint, create=True)
    mocker.patch.object(no_patch_fcf_autotrageur, '_stat_tracker', FAKE_STAT_TRACKER, create=True)
    mocker.patch.object(no_patch_fcf_autotrageur._stat_tracker, 'detach_traders')
    mocker.patch.object(no_patch_fcf_autotrageur._stat_tracker, 'attach_traders')

    # Need to mock out to prevent test dying on logging call.
    mocker.patch.object(
        no_patch_fcf_autotrageur.checkpoint, '_strategy_state', create=True)

    mocker.patch.object(uuid, 'uuid4', return_value=FAKE_NEW_STATE_UUID)
    mocker.patch.object(db_handler, 'execute_parametrized_query')
    mocker.patch.object(db_handler, 'insert_row')
    mocker.patch.object(db_handler, 'commit_all')
    mocker.patch.object(pickle, 'dumps')
    mock_copyreg_pickle = mocker.patch.object(copyreg, 'pickle')

    fcf_state_row_obj = InsertRowObject(
        FCF_STATE_TABLE,
        {
            'id': FAKE_NEW_STATE_UUID,
            'autotrageur_config_id': FAKE_CONFIG_UUID,
            'autotrageur_config_start_timestamp': FAKE_CURR_TIME,
            'state': pickle.dumps(fcf_checkpoint)
        },
        (FCF_STATE_PRIM_KEY_ID,))

    no_patch_fcf_autotrageur._export_state()

    # Ensure copyreg.pickle is called appropriately for better
    # backwards-compatibility in pickling.
    mock_copyreg_pickle.assert_called_once_with(
        autotrageur.bot.arbitrage.fcf.fcf_checkpoint.FCFCheckpoint,
        autotrageur.bot.arbitrage.fcf.fcf_checkpoint_utils.pickle_fcf_checkpoint)

    no_patch_fcf_autotrageur._stat_tracker.detach_traders.assert_called_once_with()
    assert no_patch_fcf_autotrageur.checkpoint._stat_tracker is FAKE_STAT_TRACKER
    db_handler.insert_row.assert_called_once_with(fcf_state_row_obj)
    db_handler.commit_all.assert_called_once_with()
    no_patch_fcf_autotrageur._stat_tracker.attach_traders.assert_called_once_with(
        no_patch_fcf_autotrageur.trader1, no_patch_fcf_autotrageur.trader2)


@pytest.mark.parametrize('correct_state_obj_type', [True, False])
def test_import_state(mocker, no_patch_fcf_autotrageur, fcf_checkpoint,
                      correct_state_obj_type):
    MOCK_RESULT = b'MOCK_RESULT'
    mocker.patch.object(no_patch_fcf_autotrageur, 'checkpoint', None, create=True)
    mocker.patch.object(pickle, 'loads',
        return_value=fcf_checkpoint if correct_state_obj_type else mocker.Mock())
    mock_exec_param_query = mocker.patch.object(
        db_handler, 'execute_parametrized_query', return_value=[(MOCK_RESULT,)])

    if correct_state_obj_type:
        no_patch_fcf_autotrageur._import_state(FAKE_RESUME_UUID)
        assert no_patch_fcf_autotrageur.checkpoint is fcf_checkpoint
    else:
        with pytest.raises(IncorrectStateObjectTypeError):
            no_patch_fcf_autotrageur._import_state(FAKE_RESUME_UUID)
        assert getattr(no_patch_fcf_autotrageur, 'checkpoint') is None

    mock_exec_param_query.assert_called_once_with(
        "SELECT state FROM fcf_state where id = %s;", (FAKE_RESUME_UUID,))
    pickle.loads.assert_called_once_with(MOCK_RESULT)


def test_poll_opportunity(mocker, no_patch_fcf_autotrageur):
    mock_strategy = mocker.patch.object(
        no_patch_fcf_autotrageur, '_strategy', create=True)
    no_patch_fcf_autotrageur._poll_opportunity()
    mock_strategy.poll_opportunity.assert_called_once_with()


@pytest.mark.parametrize('resume_id', [None, 'abcdef'])
def test_post_setup(mocker, no_patch_fcf_autotrageur, resume_id):
    arguments = {
        'KEYFILE': mocker.Mock(),
        '--resume_id': resume_id,
        '--pi_mode': mocker.Mock()
    }
    FAKE_BALANCE_CHECKER = mocker.Mock()
    MOCK_EXCHANGE_KEY_MAP = mocker.Mock()
    mocker.patch.object(no_patch_fcf_autotrageur, 'trader1', create=True)
    mocker.patch.object(no_patch_fcf_autotrageur, 'trader2', create=True)
    mock_parse_keyfile = mocker.patch.object(
        no_patch_fcf_autotrageur, '_FCFAutotrageur__parse_keyfile', return_value=MOCK_EXCHANGE_KEY_MAP)
    mock_setup_traders = mocker.patch.object(
        no_patch_fcf_autotrageur, '_FCFAutotrageur__setup_traders')
    mock_send_email = mocker.patch.object(no_patch_fcf_autotrageur, '_send_email')
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'twilio_cfg_path')
    parent_super = mocker.patch.object(builtins, 'super')
    mock_load_twilio = mocker.patch.object(
        no_patch_fcf_autotrageur, '_FCFAutotrageur__load_twilio')
    mock_setup_forex = mocker.patch.object(
        no_patch_fcf_autotrageur, '_FCFAutotrageur__setup_forex')
    mock_persist_config = mocker.patch.object(
        no_patch_fcf_autotrageur, '_FCFAutotrageur__persist_config')
    mock_setup_stat_tracker = mocker.patch.object(
        no_patch_fcf_autotrageur, '_FCFAutotrageur__setup_stat_tracker')
    mocker.patch.object(no_patch_fcf_autotrageur, '_stat_tracker')
    mock_attach_traders = mocker.patch.object(no_patch_fcf_autotrageur._stat_tracker, 'attach_traders')
    mock_balance_checker_constructor = mocker.patch(
        'autotrageur.bot.arbitrage.fcf_autotrageur.FCFBalanceChecker',
        return_value=FAKE_BALANCE_CHECKER)

    no_patch_fcf_autotrageur._post_setup(arguments)

    parent_super.return_value._post_setup.assert_called_once_with(arguments)
    mock_parse_keyfile.assert_called_once_with(arguments['KEYFILE'], arguments['--pi_mode'])
    mock_setup_traders.assert_called_once_with(MOCK_EXCHANGE_KEY_MAP, arguments['--resume_id'])
    mock_load_twilio.assert_called_once_with(
        no_patch_fcf_autotrageur._config.twilio_cfg_path)
    mock_setup_forex.assert_called_once_with()
    mock_persist_config.assert_called_once_with()
    mock_setup_stat_tracker.assert_called_once_with(arguments['--resume_id'])
    if resume_id:
        mock_attach_traders.assert_called_once_with(
            no_patch_fcf_autotrageur.trader1, no_patch_fcf_autotrageur.trader2)
    else:
        mock_attach_traders.assert_not_called()
    mock_balance_checker_constructor.assert_called_once_with(
        no_patch_fcf_autotrageur.trader1,
        no_patch_fcf_autotrageur.trader2,
        mock_send_email)
    assert no_patch_fcf_autotrageur.balance_checker == FAKE_BALANCE_CHECKER


def test_send_email(mocker, no_patch_fcf_autotrageur):
    FAKE_SUBJECT = 'A FAKE SUBJECT'
    FAKE_MESSAGE = 'A FAKE MESSAGE'

    mocker.patch.object(no_patch_fcf_autotrageur._config, 'email_cfg_path', 'path/to/config')
    mocker.patch('autotrageur.bot.arbitrage.fcf_autotrageur.send_all_emails')
    no_patch_fcf_autotrageur._send_email(FAKE_SUBJECT, FAKE_MESSAGE)
    autotrageur.bot.arbitrage.fcf_autotrageur.send_all_emails.assert_called_once_with(
        no_patch_fcf_autotrageur._config.email_cfg_path, FAKE_SUBJECT, FAKE_MESSAGE)


@pytest.mark.parametrize('resume_id', [FAKE_RESUME_UUID, None])
def test_setup(mocker, no_patch_fcf_autotrageur, fcf_checkpoint, resume_id):
    arguments = {
        '--resume_id': resume_id
    }
    parent_super = mocker.patch.object(builtins, 'super')
    mock_construct_strategy = mocker.patch.object(
        no_patch_fcf_autotrageur, '_FCFAutotrageur__construct_strategy')
    mock_fcf_checkpoint_constructor = mocker.patch('autotrageur.bot.arbitrage.fcf_autotrageur.FCFCheckpoint')
    mock_import_state = mocker.patch.object(no_patch_fcf_autotrageur, '_import_state')

    if resume_id:
        mocker.patch.object(no_patch_fcf_autotrageur, 'checkpoint', fcf_checkpoint, create=True)
        mock_checkpoint_config = mocker.patch.object(
            no_patch_fcf_autotrageur.checkpoint, '_config')
        mock_checkpoint_stat_tracker = mocker.patch.object(
            no_patch_fcf_autotrageur.checkpoint, '_stat_tracker', create=True)
        mock_checkpoint_restore_strategy = mocker.patch.object(
            no_patch_fcf_autotrageur.checkpoint, 'restore_strategy')

        no_patch_fcf_autotrageur._setup(arguments)

        mock_import_state.assert_called_once_with(resume_id)
        assert no_patch_fcf_autotrageur._config is mock_checkpoint_config
        assert no_patch_fcf_autotrageur._strategy is mock_construct_strategy.return_value
        mock_checkpoint_restore_strategy.assert_called_once_with(no_patch_fcf_autotrageur._strategy)
        assert no_patch_fcf_autotrageur._stat_tracker is mock_checkpoint_stat_tracker
    else:
        no_patch_fcf_autotrageur._setup(arguments)

        mock_fcf_checkpoint_constructor.assert_called_once_with(no_patch_fcf_autotrageur._config)
        assert no_patch_fcf_autotrageur.checkpoint is mock_fcf_checkpoint_constructor.return_value
        assert no_patch_fcf_autotrageur._strategy is mock_construct_strategy.return_value

    parent_super.return_value._setup.assert_called_once_with(arguments)
    mock_construct_strategy.assert_called_once_with()


@pytest.mark.parametrize('twilio_exception', [Exception, None])
@pytest.mark.parametrize('email_exception', [Exception, None])
@pytest.mark.parametrize('is_dry_run', [True, False])
@pytest.mark.parametrize('is_test_run', [True, False])
def test_alert(mocker, no_patch_fcf_autotrageur, is_dry_run, is_test_run,
               email_exception, twilio_exception):
    subject = SUBJECT_LIVE_FAILURE
    FAKE_RECIPIENT_NUMBERS = ['+12345678', '9101121314']
    FAKE_SENDER_NUMBER = '+15349875'
    mocker.patch.object(no_patch_fcf_autotrageur._config, 'dryrun', is_dry_run)
    mocker.patch.object(no_patch_fcf_autotrageur, 'is_test_run', is_test_run, create=True)
    mocker.patch.object(no_patch_fcf_autotrageur, 'twilio_config', {
        TWILIO_RECIPIENT_NUMBERS: FAKE_RECIPIENT_NUMBERS,
        TWILIO_SENDER_NUMBER: FAKE_SENDER_NUMBER
    }, create=True)
    send_email = mocker.patch.object(no_patch_fcf_autotrageur, '_send_email')
    fake_twilio_client = mocker.Mock()
    mocker.patch.object(
        no_patch_fcf_autotrageur, 'twilio_client', fake_twilio_client, create=True)
    twilio_phone = mocker.patch.object(fake_twilio_client, 'phone')

    # Set side effects if testing exceptions.
    if email_exception:
        send_email.side_effect = email_exception
    if twilio_exception:
        twilio_phone.side_effect = twilio_exception

    if email_exception or twilio_exception:
        with pytest.raises(FCFAlertError):
            no_patch_fcf_autotrageur._alert(subject)
    else:
        no_patch_fcf_autotrageur._alert(subject)

    send_email.assert_called_once_with(subject, traceback.format_exc())
    fake_twilio_client.phone.assert_called_once_with(
        [subject, DEFAULT_PHONE_MESSAGE],
        FAKE_RECIPIENT_NUMBERS,
        FAKE_SENDER_NUMBER,
        is_mock_call=is_dry_run or is_test_run)


@pytest.mark.parametrize('trade_completed', [True, False])
def test_wait(mocker, no_patch_fcf_autotrageur, trade_completed):
    MOCK_POLL_WAIT_SHORT = 2
    mock_super = mocker.patch.object(builtins, 'super')
    mock_sleep = mocker.patch.object(time, 'sleep')
    strategy = mocker.patch.object(
        no_patch_fcf_autotrageur, '_strategy', create=True)
    strategy.trade_chunker.trade_completed = trade_completed
    mocker.patch.object(
        no_patch_fcf_autotrageur._config, 'poll_wait_short', MOCK_POLL_WAIT_SHORT)

    no_patch_fcf_autotrageur._wait()

    if trade_completed:
        mock_super.return_value._wait.assert_called_once_with()
    else:
        mock_sleep.assert_called_once_with(MOCK_POLL_WAIT_SHORT)
