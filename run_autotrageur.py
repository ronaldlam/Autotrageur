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
from datetime import datetime

from docopt import docopt

from bot.arbitrage.fcf_autotrageur import FCFAutotrageur
from libs.utilities import set_autotrageur_decimal_context


def setup_logging():
    """Initialize logging."""
    logfile_name = (
        '%s.log' % str(datetime.now()).replace(' ', '_').replace('.', '_').replace(':', '_'))
    stream_format = logging.Formatter(
        "%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    file_format = logging.Formatter(
        "%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(stream_format)

    file_handler = logging.FileHandler(logfile_name)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_format)

    root_logger = logging.getLogger()
    # This must be set so that the logger does not filter prematurely.
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(stream_handler)
    root_logger.addHandler(file_handler)


if __name__ == "__main__":
    arguments = docopt(__doc__, version="Autotrageur 0.1")
    setup_logging()

    # This sets the global decimal context for the program. We aim to
    # keep precision regardless at 28 digits until either external calls
    # or output are required.
    set_autotrageur_decimal_context()
    autotrageur = FCFAutotrageur()
    autotrageur.run_autotrageur(arguments)
