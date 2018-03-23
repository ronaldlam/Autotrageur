import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


def encrypt(plaintext, password, salt=0):
    """Return encrypted data.

    Args:
        plaintext (bytes): The data to encrypt.
        password (bytes): The password to encrypt data with.
        salt (int, optional): Defaults to 0. The salt for the password.

    Returns:
        bytes: Encrypted data.
    """
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**20,
        r=8,
        p=1,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    f = Fernet(key)
    return f.encrypt(plaintext)


def decrypt(ciphertext, password, salt=0):
    """Return decrypted data.

    Args:
        ciphertext (bytes): The encrypted data.
        password (bytes): The password to encrypt data with.
        salt (int, optional): Defaults to 0. The salt for the password.

    Returns:
        bytes: The plaintext data.
    """
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**20,
        r=8,
        p=1,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    f = Fernet(key)
    return f.decrypt(ciphertext)


def to_str(bytes_or_str):
    """Return bytes from string or byte data.

    Args:
        bytes_or_str (bytes OR string): The string/byte data.

    Returns:
        string: The string.
    """
    if isinstance(bytes_or_str, bytes):
        value = bytes_or_str.decode('utf-8')
    else:
        value = bytes_or_str
    return value


def to_bytes(bytes_or_str):
    """Return string from string or byte data.

    Args:
        bytes_or_str (bytes OR string): The string/byte data.

    Returns:
        bytes: The bytes.
    """
    if isinstance(bytes_or_str, str):
        value = bytes_or_str.encode('utf-8')
    else:
        value = bytes_or_str
    return value
