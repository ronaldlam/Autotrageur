"""Automated arbitrageur

Executes trades based on simple arbitrage strategy

Usage:
    run_autotrageur.py KEYFILE PASSWORD SALT CONFIGFILE
"""

import logging

from docopt import docopt

from bot.arbitrage.fcf_autotrageur import FCFAutotrageur
from libs.utilities import set_autotrageur_decimal_context

# For debugging purposes.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    arguments = docopt(__doc__, version="Autotrageur 0.1")

    # This sets the global decimal context for the program. We aim to
    # keep precision regardless at 28 digits until either external calls
    # or output are required.
    set_autotrageur_decimal_context()
    autotrageur = FCFAutotrageur()
    autotrageur.run_autotrageur(arguments)
