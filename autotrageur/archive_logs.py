"""Log archival tool

Compresses logs into a zip file once every day.

Usage:
    archive_logs.py
"""
import logging
import os
import time
import zipfile
from datetime import datetime

import schedule
from docopt import docopt

from autotrageur.version import VERSION


def archive_logs():
    """Compresses older log files into zip file in the same directory.

    Each directory in the 'logs' directory will be searched for
    concurrent operating bot support. This method will also delete the
    old file after archiving.
    """
    logging.info('Archive start...')

    for log_dir in filter(dir_filter, os.listdir('logs')):
        path = 'logs/{}'.format(log_dir)
        archive_files = filter(lambda x: '.log.' in x, os.listdir(path))
        zip_file_name = '{}/{}.zip'.format(
            path,
            str(datetime.now())
                .replace(' ', '_').replace('.', '_').replace(':', '_'))
        zip_file = zipfile.ZipFile(
            zip_file_name, mode='w', compression=zipfile.ZIP_DEFLATED)
        for f in archive_files:
            log_file = '{}/{}'.format(path, f)
            zip_file.write(log_file)
            os.remove(log_file)

    logging.info('Archive end.')


def dir_filter(x):
    """Checks if x is a directory in the 'logs' folder.

    Args:
        x (str): The file name.

    Returns:
        bool: Whether the item is a directory.
    """
    return os.path.isdir('logs/{}'.format(x))


def main():
    """Installed entry point."""
    docopt(__doc__, version=VERSION)
    logging.basicConfig(format="%(asctime)s %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    logging.getLogger().setLevel(logging.INFO)

    logging.info('Start')
    schedule.every().day.do(archive_logs)

    while True:
        schedule.run_pending()
        time.sleep(3600)


if __name__ == '__main__':
    main()
