"""Historical minute OHLCV data to db.

Updates database with historical minute OHLCV of a trading pair.

Usage:
    spawn_ohlcv_minute.py DBINFOFILE DBPWFILE [--pi_mode] [--db_pw=DB_PW]

Options:
    --pi_mode           Whether this is to be used with the raspberry pi or on a full desktop.
    --db_pw=DB_PW       Provide a database password via command-line.  Warning: Should be used
                        with extreme caution and only for tasks such as cronjobs.

Description:
    DBINFOFILE          Database details, including database name and user.
    DBPWFILE            The encrypted file containing the database password.
"""
import getpass
import os

from docopt import docopt

import yaml

from autotrageur.analytics.history_to_db import make_fetchers, persist_to_db
from autotrageur.version import VERSION
from fp_libs.security.encryption import decrypt
from fp_libs.utilities import to_bytes, to_str


def main():
    """Installed entry point."""
    args = docopt(__doc__, version=VERSION)

    pw = args['--db_pw']
    if pw is None:
        pw = getpass.getpass()

    with open(args['DBPWFILE'], 'rb') as db_pw:
        db_password = to_str(decrypt(
            db_pw.read(),
            to_bytes(pw),
            args['--pi_mode']))

    with open(args['DBINFOFILE'], 'r') as db_info:
        db_info = yaml.safe_load(db_info)
        db_user = db_info['db_user']
        db_name = db_info['db_name']

    min_filepaths = []
    for root, dirs, files in os.walk('configs/fetch_rpi'):
        if root.endswith('minute'):
            min_filepaths.extend([os.path.join(root, filename) for filename in
                             files if root.endswith('minute')])

    hist_fetchers = make_fetchers(min_filepaths)
    persist_to_db(db_name, db_user, db_password, hist_fetchers)


if __name__ == "__main__":
    main()
