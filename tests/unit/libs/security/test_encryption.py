import pytest

from libs.security.encryption import encrypt, decrypt, SALT_LEN
import libs.security.encryption


# Mocked third parties with simplified functionality
class MockScrypt():
    def __init__(self, salt):
        self.salt = salt

    def derive(self, password):
        return password + self.salt


class MockFernet():
    def __init__(self, key):
        self.key = key

    def encrypt(self, plaintext):
        return self.key + plaintext

    def decrypt(self, ciphertext):
        # Enforce type checking, throws TypeError on mismatch
        self.key + ciphertext
        assert(self.key == ciphertext[0:len(self.key)])
        return ciphertext[len(self.key):-SALT_LEN]


def get_mock_fernet(key):
    return MockFernet(key)


def get_mock_scrypt(salt):
    return MockScrypt(salt)


# Replace libraries with mocked functions.
libs.security.encryption.get_fernet = get_mock_fernet
libs.security.encryption.get_scrypt = get_mock_scrypt


@pytest.mark.parametrize("pt, pw", [
    (b"", b""),
    (b"", b"pw"),
    (b"pt", b""),
    (b"pt", b"pw"),
    (b"plaintext", b"pw"),
    (b"very long message", b"password")
])
def test_encrypt(pt, pw):
    ct = encrypt(pt, pw)
    if len(pt) > 0:
        assert(pt == ct[-len(pt) - SALT_LEN:-SALT_LEN])
    else:
        assert(pt == b"")


@pytest.mark.parametrize("pt, pw", [
    (b"", b""),
    (b"pt", b""),
    (b"", b"pw"),
    (b"plaintext", b"pw"),
    (b"very long message", b"password")
])
def test_encrypt_no_salt(pt, pw):
    ct = encrypt(pt, pw)
    if len(pt) > 0:
        assert(pt == ct[-len(pt) - SALT_LEN:-SALT_LEN])
    else:
        assert(pt == b"")


@pytest.mark.parametrize("pt, pw", [
    ("plaintext", b"pw"),
    (b"plaintext", "pw"),
    ("plaintext", "pw"),
])
def test_bad_encrypt(pt, pw):
    with pytest.raises(TypeError):
        encrypt(pt, pw)


@pytest.fixture
def plaintext():
    return b"plaintext"


@pytest.fixture
def ciphertext():
    return encrypt(b"plaintext", b"pw")


@pytest.mark.parametrize("pw", [
    (b"pw"),
    pytest.param(b"",
        marks=pytest.mark.xfail(raises=AssertionError, strict=True))
])
def test_decrypt(plaintext, ciphertext, pw):
    assert(plaintext == decrypt(ciphertext, pw))


@pytest.mark.parametrize("ct, pw", [
    ("ciphertext", b"pw"),
    (b"ciphertext", "pw"),
    ("ciphertext", "pw")
])
def test_bad_decrypt(ct, pw):
    with pytest.raises(TypeError):
        decrypt(ct, pw)
