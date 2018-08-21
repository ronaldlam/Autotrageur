"""Database constants."""

# Table names.
FCF_AUTOTRAGEUR_CONFIG_TABLE = 'fcf_autotrageur_config'
FCF_STATE_TABLE = 'fcf_state'
FOREX_RATE_TABLE = 'forex_rate'
TRADES_TABLE = 'trades'
TRADE_OPPORTUNITY_TABLE = 'trade_opportunity'

# Table columns.
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
    'exchange1_test',
    'exchange2_test',
    'h_to_e1_max',
    'h_to_e2_max',
    'id',
    'slippage',
    'spread_min',
    'start_timestamp',
    'vol_min'
]

# Table primary keys.
FCF_AUTOTRAGEUR_CONFIG_PRIM_KEY_ID = 'id'
FCF_AUTOTRAGEUR_CONFIG_PRIM_KEY_START_TS = 'start_timestamp'
FCF_STATE_PRIM_KEY_ID = 'id'
FOREX_RATE_PRIM_KEY_ID = 'id'
TRADES_PRIM_KEY_TRADE_OPP_ID = 'trade_opportunity_id'
TRADES_PRIM_KEY_SIDE = 'side'
TRADE_OPPORTUNITY_PRIM_KEY_ID = 'id'
