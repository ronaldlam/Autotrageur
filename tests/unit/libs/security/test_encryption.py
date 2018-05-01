import pytest

from libs.security.encryption import encrypt, decrypt
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
        return ciphertext[len(self.key):]


def get_mock_fernet(key):
    return MockFernet(key)


def get_mock_scrypt(salt):
    return MockScrypt(salt)


# Replace libraries with mocked functions.
libs.security.encryption.get_fernet = get_mock_fernet
libs.security.encryption.get_scrypt = get_mock_scrypt


@pytest.mark.parametrize("pt, pw, salt", [
    (b"", b"", b""),
    (b"pt", b"", b""),
    (b"", b"pw", b""),
    (b"", b"", b"salt"),
    (b"", b"pw", b"salt"),
    (b"pt", b"", b"salt"),
    (b"pt", b"pw", b""),
    (b"plaintext", b"pw", b"salt"),
    (b"very long message", b"password", b"pepper")
])
def test_encrypt(pt, pw, salt):
    ct = encrypt(pt, pw, salt)
    if len(pt) > 0:
        assert(pt == ct[-len(pt):])
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
        assert(pt == ct[-len(pt):])
    else:
        assert(pt == b"")


@pytest.mark.parametrize("pt, pw, salt", [
    ("plaintext", b"pw", b"salt"),
    (b"plaintext", "pw", b"salt"),
    (b"plaintext", b"pw", "salt"),
    (b"plaintext", "pw", "salt"),
    ("plaintext", b"pw", "salt"),
    ("plaintext", "pw", b"salt"),
])
def test_bad_encrypt(pt, pw, salt):
    with pytest.raises(TypeError):
        encrypt(pt, pw, salt)


@pytest.fixture
def plaintext():
    return b"plaintext"


@pytest.fixture
def ciphertext():
    return encrypt(b"plaintext", b"pw", b"salt")


@pytest.mark.parametrize("pw, salt", [
    (b"pw", b"salt"),
    pytest.param(b"", b"salt",
        marks=pytest.mark.xfail(raises=AssertionError, strict=True)),
    pytest.param(b"pw", b"",
        marks=pytest.mark.xfail(raises=AssertionError, strict=True)),
    pytest.param(b"", b"",
        marks=pytest.mark.xfail(raises=AssertionError, strict=True))
])
def test_decrypt(plaintext, ciphertext, pw, salt):
    assert(plaintext == decrypt(ciphertext, pw, salt))


@pytest.mark.parametrize("ct, pw, salt", [
    ("ciphertext", b"pw", b"salt"),
    (b"ciphertext", "pw", b"salt"),
    (b"ciphertext", b"pw", "salt"),
    (b"ciphertext", "pw", "salt"),
    ("ciphertext", b"pw", "salt"),
    ("ciphertext", "pw", b"salt"),
])
def test_bad_decrypt(ct, pw, salt):
    with pytest.raises(TypeError):
        decrypt(ct, pw, salt)
