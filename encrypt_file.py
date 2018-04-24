"""Encrypt your API keys.

Creates an encrypted file encrypted-<file-name> containing of the
specified api key data.

Usage:
    encrypt_file.py FILE PASSWORD SALT
"""

from docopt import docopt

from libs.security.encryption import encrypt
from libs.utilities import to_bytes

if __name__ == "__main__":
    arguments = docopt(__doc__, version="Encrypt 0.1")
    print(arguments)

    file_name = arguments["FILE"]
    password = to_bytes(arguments["PASSWORD"])
    salt = to_bytes(arguments["SALT"])

    with open(file_name, "rb") as in_file:
        plaintext = in_file.read()
        ciphertext = encrypt(plaintext, password, salt)
        split_file_name = file_name.split("/")
        split_file_name[-1] = "encrypted-" + split_file_name[-1]
        new_file_name = "/".join(split_file_name)
        with open(new_file_name, "wb") as out_file:
            out_file.write(ciphertext)
