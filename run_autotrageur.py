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
from docopt import docopt

from bot.arbitrage.fcf_autotrageur import FCFAutotrageur
from libs.logging import autotrageur_logging as bot_logging
from libs.utilities import set_autotrageur_decimal_context

if __name__ == "__main__":
    arguments = docopt(__doc__, version="Autotrageur 0.1")

    try:
        # This sets the global decimal context for the program. We aim to
        # keep precision regardless at 28 digits until either external calls
        # or output are required.
        set_autotrageur_decimal_context()
        autotrageur = FCFAutotrageur()
        autotrageur.log_context = bot_logging.setup_background_logging()

        # Start listening for logs and run the bot.
        autotrageur.log_context.listener.start()
        autotrageur.run_autotrageur(arguments)
    finally:
        # Must be called before exit for logs to flush.
        autotrageur.log_context.listener.stop()
