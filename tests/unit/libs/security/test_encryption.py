import pytest

from libs.security.encryption import encrypt, decrypt, SALT_LEN
import libs.security.encryption


# Mocked third parties with simplified functionality
class MockScrypt():
    def __init__(self, salt, pi_mode=False):
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


def get_mock_scrypt(salt, pi_mode):
    return MockScrypt(salt, pi_mode)


# Replace libraries with mocked functions.
@pytest.fixture(scope='module')
def mock_fernet_scrypt():
    orig_get_fernet = libs.security.encryption.get_fernet
    orig_get_scrypt = libs.security.encryption.get_scrypt

    # Swap original functions to mocked functions.
    libs.security.encryption.get_fernet = get_mock_fernet
    libs.security.encryption.get_scrypt = get_mock_scrypt
    yield

    # Revert back to originals.
    libs.security.encryption.get_fernet = orig_get_fernet
    libs.security.encryption.get_scrypt = orig_get_scrypt

@pytest.fixture(scope='module')
def plaintext():
    return b"plaintext"

@pytest.fixture(scope='module')
def ciphertext():
    return encrypt(b"plaintext", b"pw")

@pytest.mark.usefixtures("mock_fernet_scrypt")
class TestEncryption():
    @pytest.mark.parametrize("pt, pw", [
        (b"", b""),
        (b"", b"pw"),
        (b"pt", b""),
        (b"pt", b"pw"),
        (b"plaintext", b"pw"),
        (b"very long message", b"password")
    ])
    def test_encrypt(self, pt, pw):
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
    def test_encrypt_no_salt(self, pt, pw):
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
    def test_bad_encrypt(self, pt, pw):
        with pytest.raises(TypeError):
            encrypt(pt, pw)

    @pytest.mark.parametrize("pw", [
        (b"pw"),
        pytest.param(b"",
            marks=pytest.mark.xfail(raises=AssertionError, strict=True))
    ])
    def test_decrypt(self, plaintext, ciphertext, pw):
        assert(plaintext == decrypt(ciphertext, pw))

    @pytest.mark.parametrize("ct, pw", [
        ("ciphertext", b"pw"),
        (b"ciphertext", "pw"),
        ("ciphertext", "pw")
    ])
    def test_bad_decrypt(self, ct, pw):
        with pytest.raises(TypeError):
            decrypt(ct, pw)
