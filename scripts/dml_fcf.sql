CREATE DATABASE IF NOT EXISTS table_history;

USE DATABASE table_history;

CREATE TABLE IF NOT EXISTS config_map (
    id VARCHAR(36) NOT NULL,
    table_name VARCHAR(40) NOT NULL,
    PRIMARY KEY (id));

CREATE TABLE IF NOT EXISTS fcf_autotrageur_config (
    id VARCHAR(36) NOT NULL,
    dryrun BIT NOT NULL,
    dryrun_e1_base DECIMAL(27, 8) UNSIGNED NOT NULL,
    dryrun_e1_quote DECIMAL(27, 8) UNSIGNED NOT NULL,
    dryrun_e2_base DECIMAL(27, 8) UNSIGNED NOT NULL,
    dryrun_e2_quote DECIMAL(27, 8) UNSIGNED NOT NULL,
    exchange1 VARCHAR(28) NOT NULL,
    exchange1_pair VARCHAR(21) NOT NULL,
    exchange1_test BIT,
    exchange2 VARCHAR(28) NOT NULL,
    exchange2_pair VARCHAR(21) NOT NULL,
    exchange2_test BIT,
    h_to_e1_max DECIMAL(18, 8) NOT NULL,
    h_to_e2_max DECIMAL(18, 8) NOT NULL,
    spread_min DECIMAL(18, 8) NOT NULL,
    vol_min DECIMAL(27, 8) UNSIGNED NOT NULL,
    slippage DECIMAL(18, 8) NOT NULL,
    start_timestamp INT(11) UNSIGNED NOT NULL,
    PRIMARY KEY (id));

CREATE TABLE IF NOT EXISTS trade_opportunity (
    id VARCHAR(36) NOT NULL,
    e1_spread DECIMAL(18, 8) NOT NULL,
    e2_spread DECIMAL(18, 8) NOT NULL,
    e1_buy DECIMAL(27, 8) NOT NULL,
    e1_sell DECIMAL(27, 8) NOT NULL,
    e2_buy DECIMAL(27, 8) NOT NULL,
    e2_sell DECIMAL(27, 8) NOT NULL,
    PRIMARY KEY (id));

CREATE TABLE IF NOT EXISTS trades (
    trade_opportunity_id VARCHAR(36) NOT NULL,
    side VARCHAR(4) NOT NULL,
    autotrageur_config_id VARCHAR(36) NOT NULL,
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
    CONSTRAINT `fk_autotrageur_config_id`
        FOREIGN KEY (autotrageur_config_id) REFERENCES fcf_autotrageur_config (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT `fk_trade_opportunity_id`
        FOREIGN KEY (trade_opportunity_id) REFERENCES trade_opportunity (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

