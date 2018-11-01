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


LOGS = 'logs'


def archive_logs():
    """Compresses older log files into zip file in the same directory.

    The bot creates log files in the following format:
    ./logs/<log-type>/<run-config-id>/<start-timestamp>/<log-files>

    Each directory in the 'logs' directory will be searched for
    concurrent operating bot support. Archives are only created if there
    logs to archive. Old files are deleted after archiving. The archives
    are created in zip files named by the timestamp at the time of
    archive, in the location of the existing files.
    """
    logging.info('Archive start...')

    log_types = [join(LOGS, d) for d in os.listdir(LOGS) if isdir(join(LOGS, d))]
    for log_type in log_types:
        runs = [join(log_type, d) for d in os.listdir(log_type) if isdir(join(log_type, d))]
        for run in runs:
            starts = [join(run, d) for d in os.listdir(run) if isdir(join(run, d))]
            for start in starts:
                archive_files = [f for f in os.listdir(start) if '.log.' in f]
                if archive_files:
                    zip_file_name = (str(datetime.now())
                        .replace(' ', '_').replace('.', '_').replace(':', '_'))
                    zip_file_path = join(start, zip_file_name + '.zip')
                    zip_file = zipfile.ZipFile(
                        zip_file_path, mode='w',
                        compression=zipfile.ZIP_DEFLATED)
                    for f in archive_files:
                        log_file = '{}/{}'.format(start, f)
                        zip_file.write(log_file, arcname=f)
                        os.remove(log_file)
                    zip_file.close()

    logging.info('Archive end.')


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
