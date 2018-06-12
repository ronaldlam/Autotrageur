"""Historical minute OHLCV data to db.

Updates database with historical minute OHLCV of a trading pair.

Usage:
    spawn_ohlcv_minute.py DBINFOFILE DBPWFILE [--pi-mode]

Options:
    --pi-mode               Whether this is to be used with the raspberry pi or on a full desktop.

Description:
    DBINFOFILE          Database details, including database name and user.
    DBPWFILE            The encrypted file containing the database password.
"""
import getpass
import os
from docopt import docopt

import yaml

from analytics.history_to_db import make_fetchers, persist_to_db
from libs.security.encryption import decrypt
from libs.utilities import to_bytes, to_str


if __name__ == "__main__":
    args = docopt(__doc__, version="spawn_ohlcv_minute 0.1")

    pw = getpass.getpass()

    with open(args['DBPWFILE'], 'rb') as db_pw:
        db_password = to_str(decrypt(
            db_pw.read(),
            to_bytes(pw),
            args['--pi-mode']))

    with open(args['DBINFOFILE'], 'r') as db_info:
        db_info = yaml.load(db_info)
        db_user = db_info['db_user']
        db_name = db_info['db_name']

    min_filepaths = []
    for root, dirs, files in os.walk('configs/fetch_rpi'):
        if root.endswith('minute'):
            min_filepaths.extend([os.path.join(root, filename) for filename in
                             files if root.endswith('minute')])

    hist_fetchers = make_fetchers(min_filepaths)
    persist_to_db(db_name, db_user, db_password, hist_fetchers)
