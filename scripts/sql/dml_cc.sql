CREATE DATABASE IF NOT EXISTS cc_trade_history;

USE cc_trade_history;

CREATE TABLE IF NOT EXISTS cc_autotrageur_config (
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
    max_trade_size DECIMAL(27, 8) UNSIGNED NOT NULL,
    spread_min DECIMAL(18, 8) NOT NULL,
    slippage DECIMAL(18, 8) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS cc_session (
    id VARCHAR(36) NOT NULL,
    start_timestamp INT(11) UNSIGNED NOT NULL,
    autotrageur_config_id VARCHAR(36) NOT NULL,
    stop_timestamp INT(11) UNSIGNED,
    PRIMARY KEY (id),
    CONSTRAINT `fk_cc_session_cc_autotrageur_config`
        FOREIGN KEY (autotrageur_config_id) REFERENCES cc_autotrageur_config (id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS cc_measures (
    id VARCHAR(36) NOT NULL,
    session_id VARCHAR(36) NOT NULL,
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
    CONSTRAINT `fk_cc_measures_cc_session`
        FOREIGN KEY (session_id) REFERENCES cc_session (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS trade_opportunity (
    id VARCHAR(36) NOT NULL,
    e1_buy_spread DECIMAL(18, 8) NOT NULL,
    e1_sell_spread DECIMAL(18, 8) NOT NULL,
    e1_buy DECIMAL(27, 8) NOT NULL,
    e1_sell DECIMAL(27, 8) NOT NULL,
    e2_buy DECIMAL(27, 8) NOT NULL,
    e2_sell DECIMAL(27, 8) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS trades (
    trade_opportunity_id VARCHAR(36) NOT NULL,
    side VARCHAR(4) NOT NULL,
    session_id VARCHAR(36) NOT NULL,
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
    CONSTRAINT `fk_trades_cc_session`
        FOREIGN KEY (session_id) REFERENCES cc_session (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT `fk_trades_trade_opportunity`
        FOREIGN KEY (trade_opportunity_id) REFERENCES trade_opportunity (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS cc_state (
    id VARCHAR(36) NOT NULL,
    session_id VARCHAR(36) NOT NULL,
    state BLOB NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT `fk_cc_state_cc_session`
        FOREIGN KEY (session_id) REFERENCES cc_session (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
