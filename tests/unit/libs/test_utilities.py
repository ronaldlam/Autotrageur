"""Test utilities.py

List of bad strings taken from:
https://github.com/minimaxir/big-list-of-naughty-strings
"""

import base64
import json
from decimal import Decimal

import pytest

from libs.utilities import (IncorrectFormatException, keyfile_to_map,
                            keys_exists, num_to_decimal,
                            set_autotrageur_decimal_context,
                            set_human_friendly_decimal_context, to_bytes,
                            to_str)

keyfile_labels = [
    "valid",
    "short param with comma",
]

bad_keyfile_labels = [
    "empty",
    "incorrect headers",
    "header typo",
    "extra param",
    "short param no comma",
]

keyfiles = [
    "exchange,api_key,api_secret\n"
    "binance,binance_api_key,binance_api_secret\n"
    "bithumb,bithumb_api_key,bithumb_api_secret\n"
    "gemini,gemini_api_key,gemini_api_secret",
    "exchange,api_key,api_secret\n"
    "binance,binance_api_key,\n"
    "bithumb,bithumb_api_key,bithumb_api_secret\n"
    "gemini,gemini_api_key,gemini_api_secret",
]

bad_keyfiles = [
    "",
    "aaa,sss,ddd",
    "exchange,api_key,api_secrets\n"
    "binance,binance_api_key,binance_api_secret\n"
    "bithumb,bithumb_api_key,bithumb_api_secret\n"
    "gemini,gemini_api_key,gemini_api_secret",
    "exchange,api_key,api_secret\n"
    "binance,binance_api_key,binance_api_secret,extra\n"
    "bithumb,bithumb_api_key,bithumb_api_secret\n"
    "gemini,gemini_api_key,gemini_api_secret",
    "exchange,api_key,api_secrets\n"
    "binance,binance_api_key\n"
    "bithumb,bithumb_api_key,bithumb_api_secret\n"
    "gemini,gemini_api_key,gemini_api_secret",
]


def naughty_strings(file_path):
    """Get the list of naughty_strings.

    Args:
        file_path (str): The file_path the the blns.txt file.

    Returns:
        list[str]: The list of naughty strings.
    """
    strings = []

    with open(file_path, 'r', encoding='utf-8') as f:
        strings = json.loads(f.read())

    return strings


def bad_strings():
    """Retrieve the bad strings.

    Returns:
        list[str]: The list of bad strings.
    """
    return naughty_strings("tests/unit/libs/blns.json")


def bad_bytes():
    """Retrieve the bad strings in bytes

    Returns:
        list[bytes]: The list of bad strings in bytes.
    """
    return [s.encode('utf-8') for s in bad_strings()]


@pytest.fixture(params=list(zip(bad_strings(), bad_bytes())))
def zipped_strs(request):
    """Pairs up strings with corresponding bytes.

    Args:
        request (FixtureRequest): Fixture describing information about
            the request; use to retrieve param data.

    Returns:
        tuple(str, bytes): The bad string and byte pair.
    """
    return request.param


@pytest.fixture(params=bad_keyfiles, ids=bad_keyfile_labels)
def bad_keyfile(request):
    """The bad keyfiles.

    Args:
        request (FixtureRequest): Fixture describing information about
            the request; use to retrieve param data.

    Returns:
        str: The bad keyfile.
    """
    return request.param


def test_str_to_bytes(zipped_strs):
    """Tests to_bytes() for str's"""
    assert(to_bytes(zipped_strs[0]) == zipped_strs[1])


def test_bytes_to_str(zipped_strs):
    """Tests to_str() for bytes'"""
    assert(zipped_strs[0] == to_str(zipped_strs[1]))


def test_both_to_str(zipped_strs):
    """Tests to_str() for both str's and bytes'"""
    assert(to_str(zipped_strs[0]) == to_str(zipped_strs[1]))


def test_both_to_bytes(zipped_strs):
    """Tests to_bytes() for both str's and bytes'"""
    assert(to_bytes(zipped_strs[0]) == to_bytes(zipped_strs[1]))


@pytest.mark.parametrize(
    "keyfile, test_id",
    list(zip(keyfiles, keyfile_labels)), ids=keyfile_labels)
def test_keyfile_to_map(keyfile, test_id):
    """Tests valid keyfiles."""
    keyfile_map = keyfile_to_map(keyfile)
    assert(keyfile_map == keyfile_to_map_result[test_id])


def test_bad_keyfile_to_map(bad_keyfile):
    """Tests invalid keyfiles."""
    with pytest.raises(IncorrectFormatException):
        keyfile_to_map(bad_keyfile)


@pytest.mark.parametrize("args", [
    ["valid"],
    ["valid", "bithumb", "api_key"],
    ["short param with comma", "gemini"]])
def test_keys_exists(args):
    """Tests keys_exists for True"""
    assert(keys_exists(keyfile_to_map_result, *args))


@pytest.mark.parametrize("dictionary, args", [
    ({}, []),
    ("hi", ["valid"]),
    (1, ["valid"])])
def test_keys_exists_attribute_error(dictionary, args):
    """Tests keys_exists for AttributeError's"""
    with pytest.raises(AttributeError):
        keys_exists(dictionary, *args)


@pytest.mark.parametrize("args", [
    ["nope"],
    ["valid", "bithumb", "api_key", "binance_api_key"],
    ["short param with comma", "gemini", "nope"]])
def test_not_keys_exists(args):
    """Tests keys_exists for False"""
    assert not(keys_exists(keyfile_to_map_result, *args))


@pytest.mark.parametrize("num, result", [
    (None, None),
    (1, Decimal('1')),
    (1.000, Decimal('1.000')),
    (125123152112513, Decimal('125123152112513')),
    (1234567890.1234567, Decimal('1234567890.1234567')),
    (-1, Decimal('-1')),
    (-1.000, Decimal('-1.000')),
    (-125123152112513, Decimal('-125123152112513')),
    (-1234567890.1234567, Decimal('-1234567890.1234567')),
    ('-1', Decimal('-1')),
    ('-1.000', Decimal('-1.000')),
    ('-125123152112513', Decimal('-125123152112513')),
    ('-1234567890.123456789012345678', Decimal('-1234567890.123456789012345678')),
    ('-1234567890.1234567890123456789', Decimal('-1234567890.1234567890123456789')),
])
def test_num_to_decimal(num, result):
    assert(num_to_decimal(num) == result)


@pytest.mark.parametrize("num, round_down_result, default_result", [
    (Decimal('1.55'), Decimal('1.5'), Decimal('1.6')),
    (Decimal('1.54'), Decimal('1.5'), Decimal('1.5')),
])
def test_set_context(num, round_down_result, default_result):
    set_autotrageur_decimal_context()
    assert(round(num, 1) == round_down_result)
    set_human_friendly_decimal_context()
    assert(round(num, 1) == default_result)
    set_autotrageur_decimal_context()


keyfile_to_map_result = {
    "valid": {
        "binance": {
            "api_key": "binance_api_key",
            "api_secret": "binance_api_secret",
        },
        "bithumb": {
            "api_key": "bithumb_api_key",
            "api_secret": "bithumb_api_secret",
        },
        "gemini": {
            "api_key": "gemini_api_key",
            "api_secret": "gemini_api_secret",
        },
    },
    "short param with comma": {
        "binance": {
            "api_key": "binance_api_key",
            "api_secret": "",
        },
        "bithumb": {
            "api_key": "bithumb_api_key",
            "api_secret": "bithumb_api_secret",
        },
        "gemini": {
            "api_key": "gemini_api_key",
            "api_secret": "gemini_api_secret",
        },
    },
}
