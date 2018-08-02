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
from libs.logging import bot_logging
from libs.utilities import set_autotrageur_decimal_context


def main(arguments):
    """Main function after `run_autotrageur` called as entry script.

    Setup:
    Sets the decimal context to deal with decimal precision and arithmetic in
    the bot.  Also sets up the background logger for logging on a separate
    thread using a queue.

    Run:
    Calls the `run_autotrageur` function to start bot's run.

    Args:
        arguments (args): The command-line arguments parsed by docopt.
    """
    try:
        # This sets the global decimal context for the program. We aim to
        # keep precision regardless at 28 digits until either external calls
        # or output are required.
        set_autotrageur_decimal_context()
        bg_logger = bot_logging.setup_background_logger()
        autotrageur = FCFAutotrageur(bg_logger)

        # Start listening for logs and run the bot.
        autotrageur.logger.queue_listener.start()
        autotrageur.run_autotrageur(arguments)
    finally:
        # Must be called before exit for logs to flush.
        autotrageur.logger.queue_listener.stop()

if __name__ == "__main__":
    arguments = docopt(__doc__, version="Autotrageur 0.1")
    main(arguments)
