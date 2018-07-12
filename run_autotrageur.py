"""Automated arbitrageur

Executes trades based on simple arbitrage strategy

Usage:
    run_autotrageur.py KEYFILE CONFIGFILE [--pi-mode]

Options:
    --pi-mode               Whether this is to be used with the raspberry pi or on a full desktop.

Description:
    KEYFILE                 The encrypted Keyfile containing relevant api keys.
    CONFIGFILE              The config file, modeled under configs/arb_config_sample.yaml for use with the bot.
    PI_MODE                 Whether this is to be used with the raspberry pi or on a full desktop.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from queue import Queue

from docopt import docopt

from bot.arbitrage.fcf_autotrageur import FCFAutotrageur
from libs.utilities import set_autotrageur_decimal_context


def setup_background_logging():
    """Initialize logging in background thread.

    Returns:
        logging.handlers.QueueListener: The background thread listener
            that passes the log records to its handlers.
    """
    name = str(datetime.now()).replace(' ', '_').replace('.', '_').replace(':', '_')
    directory_name = 'logs/{}'.format(name)
    logfile_name = '{}/{}.log'.format(directory_name, name)

    # Intentionally unprotected. If there's another log with the same
    # timestamp, there's something wrong. Go figure it out.
    os.makedirs(directory_name)

    stream_format = logging.Formatter(
        "%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    file_format = logging.Formatter(
        "%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(stream_format)

    # BackupCount is arbitrarily large, will generate approx 3tb of
    # files before rollover. We rely on external scripts to archive the
    # logs.
    file_handler = logging.handlers.TimedRotatingFileHandler(
        logfile_name, when='H', interval=4, backupCount=100000)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_format)

    queue = Queue(-1)  # no limit on size
    queue_handler = logging.handlers.QueueHandler(queue)
    listener = logging.handlers.QueueListener(
        queue, stream_handler, file_handler, respect_handler_level=True)

    root_logger = logging.getLogger()
    # This must be set so that the logger does not filter prematurely.
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(queue_handler)
    return listener


if __name__ == "__main__":
    arguments = docopt(__doc__, version="Autotrageur 0.1")

    listener = setup_background_logging()
    # Start listening for logs.
    listener.start()

    try:
        # This sets the global decimal context for the program. We aim to
        # keep precision regardless at 28 digits until either external calls
        # or output are required.
        set_autotrageur_decimal_context()
        autotrageur = FCFAutotrageur()
        autotrageur.run_autotrageur(arguments)
    finally:
        # Must be called before exit for logs to flush.
        listener.stop()
