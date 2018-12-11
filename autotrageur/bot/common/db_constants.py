"""Database constants."""

# Table names.
CC_AUTOTRAGEUR_CONFIG_TABLE = 'cc_autotrageur_config'
CC_MEASURES_TABLE = 'cc_measures'
CC_SESSION_TABLE = 'cc_session'
CC_STATE_TABLE = 'cc_state'
FCF_AUTOTRAGEUR_CONFIG_TABLE = 'fcf_autotrageur_config'
FCF_MEASURES_TABLE = 'fcf_measures'
FCF_SESSION_TABLE = 'fcf_session'
FCF_STATE_TABLE = 'fcf_state'
FOREX_RATE_TABLE = 'forex_rate'
TRADES_TABLE = 'trades'
TRADE_OPPORTUNITY_TABLE = 'trade_opportunity'

# Table columns.
CC_AUTOTRAGEUR_CONFIG_COLUMNS = [
    'dryrun',
    'dryrun_e1_base',
    'dryrun_e1_quote',
    'dryrun_e2_base',
    'dryrun_e2_quote',
    'exchange1',
    'exchange2',
    'exchange1_pair',
    'exchange2_pair',
    'use_test_api',
    'id',
    'max_trade_size',
    'slippage',
    'spread_min',
    'start_timestamp'
]
FCF_AUTOTRAGEUR_CONFIG_COLUMNS = [
    'dryrun',
    'dryrun_e1_base',
    'dryrun_e1_quote',
    'dryrun_e2_base',
    'dryrun_e2_quote',
    'exchange1',
    'exchange2',
    'exchange1_pair',
    'exchange2_pair',
    'use_test_api',
    'h_to_e1_max',
    'h_to_e2_max',
    'id',
    'max_trade_size',
    'slippage',
    'spread_min',
    'start_timestamp',
    'vol_min'
]

# Table primary keys.
CC_AUTOTRAGEUR_CONFIG_PRIM_KEY_ID = 'id'
CC_MEASURES_PRIM_KEY_ID = 'id'
CC_SESSION_PRIM_KEY_ID = 'id'
CC_STATE_PRIM_KEY_ID = 'id'
FCF_AUTOTRAGEUR_CONFIG_PRIM_KEY_ID = 'id'
FCF_MEASURES_PRIM_KEY_ID = 'id'
FCF_SESSION_PRIM_KEY_ID = 'id'
FCF_STATE_PRIM_KEY_ID = 'id'
FOREX_RATE_PRIM_KEY_ID = 'id'
TRADES_PRIM_KEY_TRADE_OPP_ID = 'trade_opportunity_id'
TRADES_PRIM_KEY_SIDE = 'side'
TRADE_OPPORTUNITY_PRIM_KEY_ID = 'id'
