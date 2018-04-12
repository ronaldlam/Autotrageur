"""Automated arbitrageur

Executes trades based on simple arbitrage strategy

Usage:
    run_autotrageur.py KEYFILE PASSWORD SALT CONFIGFILE
"""

import logging

from docopt import docopt

import autotrageur

# For debugging purposes.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    arguments = docopt(__doc__, version="Autotrageur 0.1")
    autotrageur = autotrageur.Autotrageur()
    autotrageur.run_autotrageur(arguments)