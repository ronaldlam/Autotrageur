"""Overwrites a persisted resumed state of the Autotrageur bot.

NOTE: To be used only for emergencies.  Follow the config file outline
carefully .

Usage:
    resume_overrider.py CONFIGFILE DBINFOFILE RESUME_ID

Description:
    CONFIGFILE              The input config file providing details of what parts of
                            the persisted state to override.
    DBINFOFILE              Database details, including database name and user.
    RESUME_ID               The ID of the Autotrageur state to fetch.
"""
import copy
import copyreg
import getpass
import pickle
import sys
import time
import uuid

import yaml
from docopt import docopt

import fp_libs.db.maria_db_handler as db_handler
from autotrageur.bot.arbitrage.autotrageur import Configuration
from autotrageur.bot.arbitrage.fcf.fcf_checkpoint import FCFCheckpoint
from autotrageur.bot.arbitrage.fcf.fcf_checkpoint_utils import \
    pickle_fcf_checkpoint
from autotrageur.bot.arbitrage.fcf.strategy import FCFStrategyState
from autotrageur.bot.arbitrage.fcf.target_tracker import FCFTargetTracker
from autotrageur.bot.arbitrage.fcf.trade_chunker import FCFTradeChunker
from autotrageur.bot.common.config_constants import DB_NAME, DB_USER
from autotrageur.bot.common.db_constants import (FCF_AUTOTRAGEUR_CONFIG_COLUMNS,
                                                 FCF_AUTOTRAGEUR_CONFIG_PRIM_KEY_ID,
                                                 FCF_AUTOTRAGEUR_CONFIG_PRIM_KEY_START_TS,
                                                 FCF_AUTOTRAGEUR_CONFIG_TABLE,
                                                 FCF_STATE_PRIM_KEY_ID,
                                                 FCF_STATE_TABLE)
from autotrageur.bot.common.enums import Momentum
from autotrageur.version import VERSION
from fp_libs.db.maria_db_handler import InsertRowObject
from fp_libs.utilities import num_to_decimal


def _connect_db(args):
    # Connect to the DB.
    db_password = getpass.getpass(
        prompt="Enter database password:")
    with open(args['DBINFOFILE'], 'r') as db_file:
        db_info = yaml.safe_load(db_file)
    db_handler.start_db(
        db_info[DB_USER],
        db_password,
        db_info[DB_NAME])


def _is_number(in_num):
    # `bool` is a subclass of `int` so we cannot use isinstance().
    return type(in_num) in (float, int)


def _load_checkpoint(resume_id):
    raw_result = db_handler.execute_parametrized_query(
                "SELECT state FROM fcf_state where id = %s;",
                (resume_id,))

    # The raw result comes back as a list of tuples.  We expect only
    # one result as the `autotrageur_resume_id` is unique per
    # export.
    return pickle.loads(raw_result[0][0])


def _export_checkpoint(checkpoint, new_config):
    new_checkpoint_id = str(uuid.uuid4())
    # Register copyreg.pickle with Checkpoint object and helper function
    # for better backwards-compatibility in pickling.
    # (See 'fcf_checkpoint_utils' module for more details)
    copyreg.pickle(FCFCheckpoint, pickle_fcf_checkpoint)

    # The generated ID can be used as the `resume_id` to resume the bot
    # from the saved state.
    fcf_state_map = {
        'id': new_checkpoint_id,
        'autotrageur_config_id': new_config.id,
        'autotrageur_config_start_timestamp': new_config.start_timestamp,
        'state': pickle.dumps(checkpoint)
    }
    fcf_state_row_obj = InsertRowObject(
        FCF_STATE_TABLE,
        fcf_state_map,
        (FCF_STATE_PRIM_KEY_ID,))
    db_handler.insert_row(fcf_state_row_obj)
    db_handler.commit_all()

    return new_checkpoint_id


def _export_config(new_config):
    fcf_autotrageur_config_row = db_handler.build_row(
        FCF_AUTOTRAGEUR_CONFIG_COLUMNS, new_config._asdict())
    config_row_obj = InsertRowObject(
        FCF_AUTOTRAGEUR_CONFIG_TABLE,
        fcf_autotrageur_config_row,
        (FCF_AUTOTRAGEUR_CONFIG_PRIM_KEY_ID,
        FCF_AUTOTRAGEUR_CONFIG_PRIM_KEY_START_TS))

    db_handler.insert_row(config_row_obj)
    db_handler.commit_all()


def _replace_strategy_state(checkpoint, in_yaml):
    old_ss = checkpoint.strategy_state
    new_ss_map = in_yaml['strategy_state_map']

    new_strategy_state = FCFStrategyState(
        new_ss_map['has_started'] if new_ss_map['has_started'] is not None
            else old_ss.has_started,
        num_to_decimal(new_ss_map['h_to_e1_max']) if new_ss_map['h_to_e1_max']
            is not None else old_ss.h_to_e1_max,
        num_to_decimal(new_ss_map['h_to_e2_max']) if new_ss_map['h_to_e2_max']
            is not None else old_ss.h_to_e2_max)

    new_momentum = new_ss_map['momentum']
    if new_momentum:
        for name, member in Momentum.__members__.items():
            if member.value == new_momentum:
                new_strategy_state.momentum = member
                break

        if not new_strategy_state.momentum:
            new_strategy_state.momentum = old_ss.momentum

    # Set the e1_targets and e2_targets, if present.  Else, just set to the
    # previous targets.
    for tgt_key in ['e1_targets', 'e2_targets']:
        new_tgts = []
        if in_yaml[tgt_key]:
            for price, vol in in_yaml[tgt_key]:
                # Create a tuple, with casted price and vol into Decimal type.
                new_tgts.append((num_to_decimal(price), num_to_decimal(vol)))
            setattr(new_strategy_state, tgt_key, new_tgts)
        else:
            setattr(new_strategy_state, tgt_key, getattr(old_ss, tgt_key))

    # Initialize the target_tracker and trade_chunker to the old strategy state
    # target_tracker and trade_chunker.
    new_strategy_state.target_tracker = old_ss.target_tracker
    new_strategy_state.trade_chunker = old_ss.trade_chunker

    if in_yaml['target_tracker_override']:
        new_tt_map = in_yaml['target_tracker_map']
        old_tt = old_ss.target_tracker
        new_target_tracker = FCFTargetTracker()

        for key in new_tt_map:
            setattr(new_target_tracker, key,
                new_tt_map[key] if new_tt_map[key] is not None
                else getattr(old_tt, key))

        # Replace with new target tracker.
        new_strategy_state.target_tracker = new_target_tracker

    if in_yaml['trade_chunker_override']:
        new_tc_map = in_yaml['trade_chunker_map']
        old_tc = old_ss.trade_chunker
        tc_constructor_attr = ['_max_trade_size']

        new_trade_chunker = FCFTradeChunker(
            num_to_decimal(
                new_tc_map['_max_trade_size']) if new_tc_map['_max_trade_size']
                is not None else old_tc._max_trade_size)

        for key in new_tc_map:
            if key not in tc_constructor_attr:
                new_value = (num_to_decimal(new_tc_map[key])
                    if _is_number(new_tc_map[key]) else new_tc_map[key])
                setattr(new_trade_chunker, key,
                    new_value if new_value is not None
                    else getattr(old_tc, key))

        # Replace with new trade chunker.
        new_strategy_state.trade_chunker = new_trade_chunker

    # Replace with new strategy state.
    checkpoint.strategy_state = new_strategy_state

def main():
    """Main function after `resume_fabricator` called as entry script."""
    args = docopt(__doc__, version=VERSION)

    _connect_db(args)

    # Parse the input file.
    with open(args['CONFIGFILE']) as in_file:
        in_yaml = yaml.safe_load(in_file)

    # Import the desired resume state based on ID.
    resume_id = args['RESUME_ID']
    checkpoint = _load_checkpoint(resume_id)

    # Save a copy of the old checkpoint for comparison purposes.
    original_checkpoint = copy.deepcopy(checkpoint)

    # Replace the Configuration object, if override specified.
    # Create a new ID and start_timestamp, unpack the rest of the config.
    if in_yaml['config_override']:
        new_configuration = Configuration(
            id=str(uuid.uuid4()),
            start_timestamp=int(time.time()),
            **in_yaml['config_map'])

        checkpoint._config = new_configuration

    # Replace the strategy state object, if override specified.
    if in_yaml['strategy_state_override']:
        _replace_strategy_state(checkpoint, in_yaml)

    # Final prompt before persisting back into DB.
    user_confirm = input(
        ">> You want to create from OLD checkpoint:\n"
        "*********************************************************************"
        "\n\n\n\n\n{}\n\n\n\n\nA NEW checkpoint:\n"
        "*********************************************************************"
        "\n\n\n\n\n{}\n\n\n\n\nY/N ?".format(
            original_checkpoint, checkpoint))

    if user_confirm.lower() != 'y':
        sys.exit("Resume fabrication process terminated due to no confirmation "
            "from user.")
    elif not in_yaml['config_override'] and not in_yaml['strategy_state_override']:
        sys.exit("Resume fabrication process terminated due to no desired "
            "override specified for any state.")
    else:
        # Export back to DB.
        print('#### Exporting to DB')
        _export_config(new_configuration)
        print('#### Exported new config id: {}'.format(new_configuration.id))
        new_checkpoint_id = _export_checkpoint(checkpoint, new_configuration)
        print('#### Exported new checkpoint with resume_id: {}'.format(
            new_checkpoint_id))


if __name__ == "__main__":
    main()
