from decimal import (ROUND_DOWN, ROUND_HALF_UP, Clamped, Context, Decimal,
                     DefaultContext, DivisionByZero, FloatOperation,
                     InvalidOperation, Overflow, Subnormal, Underflow,
                     getcontext, setcontext)

FIXED_KEYFILE_LABELS = ["exchange", "api_key", "api_secret", "password"]

# Context for console output.
# Note the list ordering, the + operator appends to the first list, so
# this does not change the default context.
HUMAN_READABLE_CONTEXT = Context(
    traps=[FloatOperation] + [k for k, v in DefaultContext.traps.items() if v],
    rounding=ROUND_HALF_UP          # What you learn in school.
)

# Context for trading.
AUTOTRAGEUR_CONTEXT = Context(
    traps=[
        FloatOperation,
        Overflow,
        Underflow,
        Subnormal,
        InvalidOperation,
        Clamped,
        DivisionByZero
    ],
    rounding=ROUND_DOWN             # Rounds towards zero.
)


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
            "Keyfile column headers must be {}, received {}.".format(
            FIXED_KEYFILE_LABELS,
            labels))

    # Checks if the last character of the file was parsed a newline character
    # '\n' and truncates the list of rows by 1 if present.
    if not rows[-1]:
        rows = rows[:-1]
    for row in rows[1:]:
        cells = row.split(",")
        if len(cells) != len(FIXED_KEYFILE_LABELS):
            raise IncorrectFormatException(
                "Incorrect number of elements in row: %s", cells)
        exchange_map[cells[0]] = dict(zip(labels[1:], cells[1:]))

    return exchange_map


def split_symbol(symbol):
    """Get base/quote from symbol.

    Args:
        symbol (str): The symbol of the market (ie. ETH/USD).

    Returns:
        [str, str]: The list of base and quote strs.
    """
    return symbol.upper().split('/')


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


def num_to_decimal(num):
    """Return decimal object given float, int or str input.

    Args:
        num (float/int/str): The input.

    Raises:
        InvalidOperation: If num cannot be converted.

    Returns:
        Decimal: The Decimal representation of the float.
    """
    if num is None:
        return None

    return Decimal(str(num))


def set_autotrageur_decimal_context():
    """Set the default Autotrageur decimal context for trading usage."""
    setcontext(AUTOTRAGEUR_CONTEXT)


def set_human_friendly_decimal_context():
    """Set the intuitive decimal context for console output usage."""
    setcontext(HUMAN_READABLE_CONTEXT)
