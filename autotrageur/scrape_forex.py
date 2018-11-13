"""Scrape forex data and insert into db.

Usage:
    scrape_forex.py DBINFOFILE FOREXINFOFILE

Description:
    DBINFOFILE          Database details, including database name and user.
    FOREXINFOFILE       Config file containing forex pairs to scrape.
"""
import getpass
import logging
import time

import schedule
import yaml
from docopt import docopt

from autotrageur.analytics.forex_to_db import (get_pairs, persist_to_db,
                                               prepare_tables, start_db)
from autotrageur.version import VERSION


def main():
    """Installed entry point."""
    args = docopt(__doc__, version=VERSION)
    logging.basicConfig(format="%(asctime)s %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    logging.getLogger().setLevel(logging.INFO)

    with open(args['DBINFOFILE'], 'r') as db_info:
        db_info = yaml.safe_load(db_info)
        db_user = db_info['db_user']
        db_name = db_info['db_name']

    db_password = getpass.getpass('DB password:')
    pairs = get_pairs(args['FOREXINFOFILE'])

    start_db(db_user, db_password, db_name)
    prepare_tables(pairs)
    schedule.every().minute.do(persist_to_db, pairs)

    while True:
        schedule.run_pending()
        time.sleep(10)


if __name__ == "__main__":
    main()
