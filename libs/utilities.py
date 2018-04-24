
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

    for row in rows[1:]:
        cells = row.split(",")
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
    """Check if *args (nested) exists in `dictionary` (dict).

    Args:
        dictionary (dict): The dict to search

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
            _dictionary = _dictionary[key]
        except KeyError:
            return False
    return True
