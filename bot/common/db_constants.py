"""Database constants."""

# Table names.
FCF_AUTOTRAGEUR_CONFIG_TABLE = 'fcf_autotrageur_config'
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

