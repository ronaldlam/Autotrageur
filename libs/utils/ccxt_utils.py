import logging
import time

from ccxt import ExchangeError, NetworkError

MAX_RETRIES = 3
WAIT_SECONDS = 1
DEFAULT_ARG_LIST = [()]
DEFAULT_KWARG_LIST = [{}]


class RetryableError(Exception):
    """ccxt.ExchangeError wrapper for retryable exceptions.

    This is to be handled at the autotrageur level.
    """
    pass


class RetryCounter():
    """An asymmetric counter for current number of available retries.

    Increments are called on successful polls, and will increment the
    internal counter to 10. Decrements are issued on errors, and will
    subtract 3 from the internal counter. If the internal counter goes
    below zero, the retries are counted as used up and the the bot will
    be stopped.

    Note that constants are picked arbitrarily, and mechanism is roughly
    modelled after Kraken's rate limiting:
    https://support.kraken.com/hc/en-us/articles/206548367-What-is-the-API-call-rate-limit-
    """
    COUNTER_MAX = 10

    def __init__(self):
        """Constructor."""
        self._counter = self.COUNTER_MAX

    def increment(self):
        """Increment internal counter by one if less than ten, no op
        otherwise.
        """
        if self._counter < self.COUNTER_MAX:
            self._counter += 1

    def decrement(self):
        """Decrement internal counter by three and check if it goes
        below 0.

        Returns:
            bool: Whether the internal counter is 'greater or equal to' 0.
        """
        self._counter -= 3
        return self._counter >= 0


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

    Raises:
        NetworkError: After `MAX_RETRIES` number of retries, the NetworkError
            is raised to its caller.

    Returns:
        list: A list of returned function results.
    """
    if len(funclist) == 0:
        logging.warning("Warning: An empty list of functions have been "
            "provided for wrap_ccxt_retry.")
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
        except ExchangeError as exchange_err:
            logging.error(exchange_err, exc_info=True)
            raise RetryableError(ExchangeError)

    if saved_exc:
        raise saved_exc
