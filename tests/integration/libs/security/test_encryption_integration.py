import pytest

from cryptography.fernet import InvalidToken
from cryptography.hazmat.backends import default_backend

from libs.security.encryption import encrypt, decrypt, SALT_LEN
import libs.security.encryption as rnd_encryption


ENCRYPT_DECRYPT_PARAMS = [
    (b"some plaintext", b"sekretpw", True),
    (b"plaintext", b"ITZASEKRET", False)
]

@pytest.mark.parametrize("salt, pi_mode", [
    (b"randomsalt", False),
    (b"randomsalt2", True)
])
def test_get_scrypt(mocker, salt, pi_mode):
    mocker.spy(rnd_encryption, 'Scrypt')
    rnd_encryption.get_scrypt(salt, pi_mode)
    if pi_mode:
        rnd_encryption.Scrypt.assert_called_with(   # pylint: disable=no-member
            salt=salt, length=32, n=2**14, r=8, p=1, backend=default_backend())
    else:
        rnd_encryption.Scrypt.assert_called_with(   # pylint: disable=no-member
            salt=salt, length=32, n=2**20, r=8, p=1, backend=default_backend())


@pytest.mark.parametrize("plaintext, password, pi_mode", ENCRYPT_DECRYPT_PARAMS)
def test_encrypt_decrypt(plaintext, password, pi_mode):
    ciphertext = encrypt(plaintext, password, pi_mode)
    assert len(ciphertext) == 132

    decrypted_text = decrypt(ciphertext, password, pi_mode)
    assert plaintext == decrypted_text


@pytest.mark.parametrize("plaintext, password, pi_mode", ENCRYPT_DECRYPT_PARAMS)
def test_encrypt_decrypt_bad_pw(plaintext, password, pi_mode):
    ciphertext = encrypt(plaintext, password, pi_mode)
    assert len(ciphertext) == 132

    with pytest.raises(InvalidToken):
        decrypt(ciphertext, b"Another Password", pi_mode)