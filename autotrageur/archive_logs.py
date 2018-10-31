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
from os.path import isdir, join

import schedule
from docopt import docopt

from autotrageur.version import VERSION


def archive_logs():
    """Compresses older log files into zip file in the same directory.

    The bot creates log files in the following format:
    ./logs/<log-type>/<run-config-id>/<start-timestamp>/<log-files>

    Each directory in the 'logs' directory will be searched for
    concurrent operating bot support. Archives are only created if there
    logs to archive. Old files are deleted after archiving.
    """
    logging.info('Archive start...')

    log_types = [d for d in os.listdir('logs') if isdir(join('logs', d))]
    for log_type in log_types:
        runs = [d for d in os.listdir(log_type) if isdir(join(log_type, d))]
        for run in runs:
            starts = [d for d in os.listdir(run) if isdir(join(run, d))]
            for start in starts:
                path = join('logs', log_type, run, start)
                archive_files = [f for f in os.listdir(path) if '.log.' in f]
                if archive_files:
                    zip_file_name = (str(datetime.now())
                        .replace(' ', '_').replace('.', '_').replace(':', '_'))
                    zip_file_path = join(path, zip_file_name + '.zip')
                    zip_file = zipfile.ZipFile(
                        zip_file_path, mode='w',
                        compression=zipfile.ZIP_DEFLATED)
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
