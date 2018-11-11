CREATE DATABASE IF NOT EXISTS fcf_trade_history;

USE fcf_trade_history;

CREATE TABLE IF NOT EXISTS fcf_autotrageur_config (
    id VARCHAR(36) NOT NULL,
    start_timestamp INT(11) UNSIGNED NOT NULL,
    dryrun BIT NOT NULL,
    dryrun_e1_base DECIMAL(27, 8) UNSIGNED NOT NULL,
    dryrun_e1_quote DECIMAL(27, 8) UNSIGNED NOT NULL,
    dryrun_e2_base DECIMAL(27, 8) UNSIGNED NOT NULL,
    dryrun_e2_quote DECIMAL(27, 8) UNSIGNED NOT NULL,
    exchange1 VARCHAR(28) NOT NULL,
    exchange1_pair VARCHAR(21) NOT NULL,
    exchange2 VARCHAR(28) NOT NULL,
    exchange2_pair VARCHAR(21) NOT NULL,
    use_test_api BIT,
    h_to_e1_max DECIMAL(18, 8) NOT NULL,
    h_to_e2_max DECIMAL(18, 8) NOT NULL,
    max_trade_size DECIMAL(27, 8) UNSIGNED NOT NULL,
    spread_min DECIMAL(18, 8) NOT NULL,
    vol_min DECIMAL(27, 8) UNSIGNED NOT NULL,
    slippage DECIMAL(18, 8) NOT NULL,
    PRIMARY KEY (id, start_timestamp)
);

CREATE TABLE IF NOT EXISTS fcf_measures (
    id VARCHAR(36) NOT NULL,
    autotrageur_config_id VARCHAR(36) NOT NULL,
    autotrageur_config_start_timestamp INT(11) UNSIGNED NOT NULL,
    autotrageur_stop_timestamp INT(11) UNSIGNED,
    e1_start_bal_base DECIMAL(27, 8) NOT NULL,
    e1_close_bal_base DECIMAL(27, 8) NOT NULL,
    e2_start_bal_base DECIMAL(27, 8) NOT NULL,
    e2_close_bal_base DECIMAL(27, 8) NOT NULL,
    e1_start_bal_quote DECIMAL(27, 8) NOT NULL,
    e1_close_bal_quote DECIMAL(27, 8) NOT NULL,
    e2_start_bal_quote DECIMAL(27, 8) NOT NULL,
    e2_close_bal_quote DECIMAL(27, 8) NOT NULL,
    num_fatal_errors INT(9) UNSIGNED NOT NULL,
    trade_count INT(11) UNSIGNED NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT `fk_fcf_measures_fcf_autotrageur_config`
        FOREIGN KEY (autotrageur_config_id, autotrageur_config_start_timestamp) REFERENCES fcf_autotrageur_config (id, start_timestamp)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS forex_rate (
    id VARCHAR(36) NOT NULL,
    quote VARCHAR(10) NOT NULL,
    rate DECIMAL(27, 8) NOT NULL,
    local_timestamp INT(11) UNSIGNED NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS trade_opportunity (
    id VARCHAR(36) NOT NULL,
    e1_spread DECIMAL(18, 8) NOT NULL,
    e2_spread DECIMAL(18, 8) NOT NULL,
    e1_buy DECIMAL(27, 8) NOT NULL,
    e1_sell DECIMAL(27, 8) NOT NULL,
    e2_buy DECIMAL(27, 8) NOT NULL,
    e2_sell DECIMAL(27, 8) NOT NULL,
    e1_forex_rate_id VARCHAR(36),
    e2_forex_rate_id VARCHAR(36),
    PRIMARY KEY (id),
    CONSTRAINT `fk_trade_opportunity_forex_rate_id_e1`
        FOREIGN KEY (e1_forex_rate_id) REFERENCES forex_rate (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT `fk_trade_opportunity_forex_rate_id_e2`
        FOREIGN KEY (e2_forex_rate_id) REFERENCES forex_rate (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS trades (
    trade_opportunity_id VARCHAR(36) NOT NULL,
    side VARCHAR(4) NOT NULL,
    autotrageur_config_id VARCHAR(36) NOT NULL,
    autotrageur_config_start_timestamp INT(11) UNSIGNED NOT NULL,
    exchange VARCHAR(28) NOT NULL,
    base VARCHAR(10) NOT NULL,
    quote VARCHAR(10) NOT NULL,
    pre_fee_base DECIMAL(27, 8) NOT NULL,
    pre_fee_quote DECIMAL(27, 8) NOT NULL,
    post_fee_base DECIMAL(27, 8) NOT NULL,
    post_fee_quote DECIMAL(27, 8) NOT NULL,
    fees DECIMAL(27, 8) NOT NULL,
    fee_asset VARCHAR(10) NOT NULL,
    price DECIMAL(27, 8) NOT NULL,
    true_price DECIMAL(27, 8) NOT NULL,
    type VARCHAR(6) NOT NULL,
    order_id VARCHAR(64) NOT NULL,
    exchange_timestamp INT(11) UNSIGNED NOT NULL,
    local_timestamp INT(11) UNSIGNED NOT NULL,
    extra_info VARCHAR(256),
    PRIMARY KEY (trade_opportunity_id, side),
    CONSTRAINT `fk_trades_fcf_autotrageur_config`
        FOREIGN KEY (autotrageur_config_id, autotrageur_config_start_timestamp) REFERENCES fcf_autotrageur_config (id, start_timestamp)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT `fk_trades_trade_opportunity`
        FOREIGN KEY (trade_opportunity_id) REFERENCES trade_opportunity (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS fcf_state (
    id VARCHAR(36) NOT NULL,
    autotrageur_config_id VARCHAR(36) NOT NULL,
    autotrageur_config_start_timestamp INT(11) UNSIGNED NOT NULL,
    state BLOB NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT `fk_fcf_state_fcf_autotrageur_config`
        FOREIGN KEY (autotrageur_config_id, autotrageur_config_start_timestamp) REFERENCES fcf_autotrageur_config (id, start_timestamp)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
