FIXED_KEYFILE_LABELS = ["exchange", "api_key", "api_secret"]


class IncorrectFormatException(Exception):
    pass


def keyfile_to_map(keyfile):
    """Convert key file data into map.

    Args:
        keyfile (string): The key file data in CSV form.

    Returns:
        dict[string:dict[string:string]]: Map from exchange to map of
            labels to API keys and secrets
    """
    exchange_map = {}
    rows = keyfile.split("\n")
    labels = rows[0].split(",")

    if FIXED_KEYFILE_LABELS != labels:
        raise IncorrectFormatException(
            "Keyfile column headers must be %s, received %s.",
            FIXED_KEYFILE_LABELS,
            labels)

    for row in rows[1:]:
        cells = row.split(",")
        if len(cells) != 3:
            raise IncorrectFormatException(
                "Incorrect number of elements in row: %s", cells)
        exchange_map[cells[0]] = {labels[1]: cells[1], labels[2]: cells[2]}

    return exchange_map


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


def keys_exists(dictionary, *keys):
    """Check if *keys (nested) exists in `dictionary` (dict).

    Args:
        dictionary (dict): The dict to search.
        keys (list): The keys in order to search the dict with.

    Raises:
        AttributeError: If dictionary is not a dict.
        AttributeError: If there are no keys to search for.

    Returns:
        bool: Whether the key is found.
    """
    if type(dictionary) is not dict:
        raise AttributeError('keys_exists() expects dict as first argument.')
    if len(keys) == 0:
        raise AttributeError(
            'keys_exists() expects at least two arguments, one given.')

    _dictionary = dictionary
    for key in keys:
        try:
            # The line after the statement may try to use the []
            # operator on an arbitrary type, perhaps yielding a
            # TypeError or other undefined behaviour.
            if type(_dictionary) is not dict:
                return False
            _dictionary = _dictionary[key]
        except KeyError:
            return False
    return True
