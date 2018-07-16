import logging
import time

from ccxt import NetworkError


MAX_RETRIES = 3
WAIT_SECONDS = 1
DEFAULT_ARG_LIST = [()]
DEFAULT_KWARG_LIST = [{}]


def wrap_ccxt_retry(funclist, arglist=DEFAULT_ARG_LIST,
                    kwarglist=DEFAULT_KWARG_LIST):
    """Wraps a CCXT API call to retry if a NetworkError is encountered.

    From: https://github.com/ccxt/ccxt/wiki/Manual#error-handling, any form of
    `NetworkError` is recoverable in the CCXT library.  We retry the given list
    of function(s) `MAX_RETRIES` number of times, with `WAIT_SECONDS` in
    between.

    NOTE: It is the caller's responsibility to ensure that the lengths of
    arglist and kwarglist are the same as funclist.

    Args:
        funclist (list): A list of functions to retry.
        arglist (list): A list of `args` which correspond to funclist in order.
        kwarglist (list): A list of `kwargs` which correspond to funclist in
            order.

    Returns:
        list: A list of returned function results.
    """
    if arglist == DEFAULT_ARG_LIST:
        arglist = DEFAULT_ARG_LIST * len(funclist)
    if kwarglist == DEFAULT_KWARG_LIST:
        kwarglist = DEFAULT_KWARG_LIST * len(funclist)

    for _ in range(MAX_RETRIES):
        func_returns = []
        try:
            for i, func in enumerate(funclist):
                func_returns.append(func(*arglist[i], **kwarglist[i]))

            return func_returns
        except NetworkError as network_err:
            logging.error(network_err, exc_info=True)
            time.sleep(WAIT_SECONDS)
            saved_exc = network_err

    raise saved_exc
