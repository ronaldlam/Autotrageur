"""Automated arbitrageur

Executes trades based on simple arbitrage strategy

Usage:
    run_autotrageur.py KEYFILE (--resume_id=FCF_STATE_ID | CONFIGFILE) DBCONFIGFILE [--pi_mode]

Options:
    --pi_mode                           Whether this is to be used with the raspberry pi or on a full desktop.
    --resume_id=FCF_STATE_ID            If provided, this bot run is continued from a previous run with FCF_STATE_ID.

Description:
    KEYFILE                             The encrypted Keyfile containing relevant api keys.
    CONFIGFILE                          The config file, modeled under configs/arb_config_sample.yaml for use with the autotrageur.bot.
    DBCONFIGFILE                        The config file for the database.
"""
from docopt import docopt

from autotrageur.bot.arbitrage.fcf_autotrageur import FCFAutotrageur
from autotrageur.version import VERSION
from fp_libs.logging import bot_logging
from fp_libs.utilities import set_autotrageur_decimal_context


def main():
    """Main function after `run_autotrageur` called as entry script.

    Setup:
    Sets the decimal context to deal with decimal precision and arithmetic in
    the bot.  Also sets up the background logger for logging on a separate
    thread using a queue.

    Run:
    Calls the `run_autotrageur` function to start bot's run.
    """
    arguments = docopt(__doc__, version=VERSION)

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
    main()
