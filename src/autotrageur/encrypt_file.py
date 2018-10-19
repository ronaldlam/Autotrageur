"""Encrypt your API keys.

Creates an encrypted file encrypted-<file-name> containing of the
specified api key data.

Usage:
    encrypt_file.py FILE [--pi_mode]

Options:
    --pi_mode               Whether this is to be used with the raspberry pi or on a full desktop.

Description:
    FILE                    The file to encrypt, with plaintext.
"""
import getpass

from docopt import docopt

from fp_libs.security.encryption import encrypt
from fp_libs.utilities import to_bytes

if __name__ == "__main__":
    arguments = docopt(__doc__, version="Encrypt 0.1")

    pw = getpass.getpass()

    file_name = arguments["FILE"]
    password = to_bytes(pw)
    pi_mode = arguments["--pi_mode"]

    with open(file_name, "rb") as in_file:
        plaintext = in_file.read()
        ciphertext = encrypt(plaintext, password, pi_mode)
        split_file_name = file_name.split("/")
        split_file_name[-1] = "encrypted-" + split_file_name[-1]
        new_file_name = "/".join(split_file_name)
        with open(new_file_name, "wb") as out_file:
            out_file.write(ciphertext)
