"""Historical minute OHLCV data to db.

Updates database with historical minute OHLCV of a trading pair.

Usage:
    spawn_ohlcv_minute.py DBINFOFILE EMAILCFGPATH [--db_pw=DB_PW]

Options:
    --db_pw=DB_PW       Provide a database password via command-line.  Warning: Should be used
                        with extreme caution and only for tasks such as cronjobs.

Description:
    DBINFOFILE          Database details, including database name and user.
    EMAILCFGPATH        Email configuration path for emailing any errors.
"""
import getpass
import logging
import os
import time

import schedule
import yaml
from docopt import docopt

import fp_libs.db.maria_db_handler as db_handler
from autotrageur.analytics.history_to_db import (HistoryTableMetadata,
                                                 make_fetchers, persist_to_db,
                                                 prepare_tables)
from autotrageur.version import VERSION

DB_KEEP_ALIVE_HOURS = 4
MINUTE_FETCH_HOURS = 8


def fetch_minute_data(email_cfg_path):
    min_filepaths = []
    for root, dirs, files in os.walk('configs/fetch_rpi'):
        if root.endswith('minute'):
            min_filepaths.extend([os.path.join(root, filename) for filename in
                             files if root.endswith('minute')])

    hist_fetchers = make_fetchers(min_filepaths)

    # Create Table Metadata objects from each type of fetcher.
    table_metadata_list = []
    for fetcher in hist_fetchers:
        table_metadata_list.append(HistoryTableMetadata(
            fetcher.base,
            fetcher.quote,
            fetcher.exchange,
            fetcher.interval,
            ''.join(
                [
                    fetcher.exchange,
                    fetcher.base,
                    fetcher.quote,
                    fetcher.interval
                ])))

    prepare_tables(table_metadata_list)
    persist_to_db(hist_fetchers, email_cfg_path)

def main():
    """Installed entry point."""
    args = docopt(__doc__, version=VERSION)
    logging.basicConfig(format="%(asctime)s %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    logging.getLogger().setLevel(logging.INFO)

    db_pw = args['--db_pw'] or getpass.getpass("Enter DB Password:")

    with open(args['DBINFOFILE'], 'r') as db_info:
        db_info = yaml.safe_load(db_info)
        db_user = db_info['db_user']
        db_name = db_info['db_name']

    # Connect to the DB.
    logging.info("DB started.")
    db_handler.start_db(db_user, db_pw, db_name)

    # Keep the DB alive.
    schedule.every(4).hours.do(db_handler.ping_db)

    # Schedule minute fetching.
    schedule.every(8).hours.do(fetch_minute_data, args['EMAILCFGPATH'])

    while True:
        schedule.run_pending()
        time.sleep(3600)


if __name__ == "__main__":
    main()
