USE fcf_trade_history;

CREATE TABLE IF NOT EXISTS forex_rate (
    id VARCHAR(36) NOT NULL,
    quote VARCHAR(10) NOT NULL,
    rate DECIMAL(27, 8) NOT NULL,
    local_timestamp INT(11) UNSIGNED NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE trade_opportunity
    ADD COLUMN IF NOT EXISTS (
        e1_forex_rate_id VARCHAR(36),
        e2_forex_rate_id VARCHAR(36)
    ),
    ADD CONSTRAINT `fk_e1_forex_rate_id`
        FOREIGN KEY IF NOT EXISTS (e1_forex_rate_id) REFERENCES forex_rate (id)
            ON DELETE RESTRICT
            ON UPDATE CASCADE,
    ADD CONSTRAINT `fk_e2_forex_rate_id`
        FOREIGN KEY IF NOT EXISTS (e2_forex_rate_id) REFERENCES forex_rate (id)
            ON DELETE RESTRICT
            ON UPDATE CASCADE
;