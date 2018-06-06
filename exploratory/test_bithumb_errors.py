import time

import pytest
import ccxt
from googletrans import Translator


@pytest.fixture(scope="session")
def translator():
    """Retrieve a Translator.

    Returns:
        googletrans.Translator: Translator for foreign language error
            messages.
    """
    return Translator()


@pytest.fixture(scope="module")
def bithumb():
    """Retrieve the ccxt bithumb object with the given credentials.

    The given account is a test account linked to
    pythonexperiment0@gmail.com. It will never hold any funds.

    Returns:
        ccxt.exchange: The authenticated bithumb exchange
    """
    # These credentials were created specifically for this purpose.
    # Reuse ONLY FOR TESTING.
    configs = {
        "apiKey": "586ac9288b6c46c22349aedca086b8ee",
        "secret": "7b424e10557f54b9f0c7a6648d311513"
    }
    exchange = ccxt.bithumb(configs)
    exchange.load_markets()
    return exchange


@pytest.fixture(params=[0.01, 0.0001, 0.00001])
def limit_amount(request):
    """Fixture indicating the amount to market orders.

    For determining limits of market orders.

    Args:
        request (FixtureRequest): Fixture describing information about
            the request; use to retrieve param data.

    Returns:
        float: An amount to market order.
    """
    return request.param


@pytest.fixture(params=[0.1111, 0.11111])
def precision_amount(request):
    """Fixture indicating the amount to market orders.

    For determining precision of market orders.

    Args:
        request (FixtureRequest): Fixture describing information about
            the request; use to retrieve param data.

    Returns:
        float: An amount to market order.
    """
    return request.param


@pytest.fixture(params=["BTC/KRW", "ETH/KRW"])
def symbol(request):
    """Symbol of the market to trade.

    Args:
        request (FixtureRequest): Fixture describing information about
            the request; use to retrieve param data.

    Returns:
        str: A market symbol.
    """
    return request.param


@pytest.fixture(params=[True, False])
def is_buy(request):
    """Whether to buy or sell.

    Args:
        request (FixtureRequest): Fixture describing information about
            the request; use to retrieve param data.

    Returns:
        bool: Whether a buy or not.
    """
    return request.param


def get_result_from_error(e, translator):
    """Retrieve translated string result from error

    Args:
        e (ccxt.ExchangeError): The error raised by ccxt.

    Returns:
        str: The translated result.
    """
    # Error messages come back with unicode escapes in the JSON. We
    # decode by decoding the binary form with the extra setting.
    decoded = e.args[0].encode('utf-8').decode('unicode_escape')
    return str(translator.translate(decoded))


def wait_out_ddos(wait_time):
    """Wait for wait_time and return wait_time.

    This will fail the test after max wait limit is reached.

    Args:
        wait_time (int): Number of seconds to wait.

    Returns:
        int: Number of seconds to wait next time.
    """
    time.sleep(wait_time)
    wait_time *= 2
    assert(wait_time <= 32)
    return wait_time


def test_get_exchange(bithumb):
    """Basic test for fixture understanding.

    Args:
        bithumb (ccxt.exchange): Fixture to be used for this module
    """
    assert(bithumb.id == 'bithumb')


def test_has_market_order(bithumb):
    assert(bithumb.has['createMarketOrder'])


def test_min_market_order_limits(
        is_buy, bithumb, symbol, limit_amount, translator, wait_time=1):
    try:
        # To avoid DDoS protection.
        time.sleep(.1)
        if is_buy:
            bithumb.create_market_buy_order(symbol, limit_amount)
        else:
            bithumb.create_market_sell_order(symbol, limit_amount)
    except ccxt.ExchangeError as e:
        result = get_result_from_error(e, translator)
        assert(result == limit_results(is_buy, symbol, limit_amount))
    except ccxt.DDoSProtection as e:
        wait_time = wait_out_ddos(wait_time)
        test_min_market_order_limits(
            is_buy, bithumb, symbol, limit_amount, translator, wait_time)


def test_max_market_order_precision(
        is_buy, bithumb, symbol, precision_amount, translator, wait_time=1):
    try:
        # To avoid DDoS protection.
        time.sleep(.1)
        if is_buy:
            bithumb.create_market_buy_order(symbol, precision_amount)
        else:
            bithumb.create_market_sell_order(symbol, precision_amount)
    except ccxt.ExchangeError as e:
        result = get_result_from_error(e, translator)
        assert(result == precision_results(is_buy, symbol, precision_amount))
    except ccxt.DDoSProtection as e:
        wait_time = wait_out_ddos(wait_time)
        test_max_market_order_precision(
            is_buy, bithumb, symbol, precision_amount, translator, wait_time)



# Failures are from dynamically calculated limits based on current
# market price. See error messages for examples.
@pytest.mark.parametrize(
    "is_buy, symbol, price", [
        pytest.param(True, "BTC/KRW", 0, marks=pytest.mark.xfail),
        (True, "BTC/KRW", 0.1),
        (True, "BTC/KRW", 1),
        pytest.param(True, "BTC/KRW", 1000, marks=pytest.mark.xfail),
        pytest.param(True, "ETH/KRW", 0, marks=pytest.mark.xfail),
        (True, "ETH/KRW", 0.1),
        (True, "ETH/KRW", 1),
        pytest.param(True, "ETH/KRW", 1000, marks=pytest.mark.xfail),
        (False, "BTC/KRW", 0),
        (False, "BTC/KRW", 0.1),
        (False, "BTC/KRW", 1),
        (False, "BTC/KRW", 1000),
        (False, "ETH/KRW", 0),
        (False, "ETH/KRW", 0.1),
        (False, "ETH/KRW", 1),
        (False, "ETH/KRW", 1000)])
def test_limit_order_min_price(
    is_buy, bithumb, symbol, price, translator, wait_time=1):
    try:
        # To avoid DDoS protection.
        time.sleep(.1)
        if (is_buy):
            bithumb.create_limit_buy_order(symbol, 0.01, price)
        else:
            bithumb.create_limit_sell_order(symbol, 0.01, price)
    except ccxt.ExchangeError as e:
        result = get_result_from_error(e, translator)
        assert(result == price_limit_results(is_buy, symbol, price))
    except ccxt.DDoSProtection as e:
        wait_time = wait_out_ddos(wait_time)
        test_limit_order_min_price(
            is_buy, bithumb, symbol, price, translator, wait_time)



def limit_results(is_buy, symbol, limit_amount):
    return {
        True: {
            "BTC/KRW": {
                0.01: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "Purchase amount exceeds usable KRW"}, pronunciation=None)',
                0.0001: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "The minimum purchase quantity is 0.001 BTC."}, pronunciation=None)',
                0.00001: 'Translated(src=en, dest=en, text=bithumb {"status":"5500","message":"Invalid Parameter"}, pronunciation=bithumb {"status":"5500","message":"Invalid Parameter"})',
            },
            "ETH/KRW": {
                0.01: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "Purchase amount exceeds usable KRW"}, pronunciation=None)',
                0.0001: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "The minimum purchase quantity is 0.01 ETH."}, pronunciation=None)',
                0.00001: 'Translated(src=en, dest=en, text=bithumb {"status":"5500","message":"Invalid Parameter"}, pronunciation=bithumb {"status":"5500","message":"Invalid Parameter"})',
            }
        },
        False: {
            "BTC/KRW": {
                0.01: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "Order has exceeded available BTC"}, pronunciation=None)',
                0.0001: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "The minimum quantity sold is 0.001 BTC."}, pronunciation=None)',
                0.00001: 'Translated(src=en, dest=en, text=bithumb {"status":"5500","message":"Invalid Parameter"}, pronunciation=bithumb {"status":"5500","message":"Invalid Parameter"})',
            },
            "ETH/KRW": {
                0.01: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "Order has exceeded the available ETH"}, pronunciation=None)',
                0.0001: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "The minimum quantity sold is 0.01 ETH."}, pronunciation=None)',
                0.00001: 'Translated(src=en, dest=en, text=bithumb {"status":"5500","message":"Invalid Parameter"}, pronunciation=bithumb {"status":"5500","message":"Invalid Parameter"})',
            }
        }
    }[is_buy][symbol][limit_amount]


def precision_results(is_buy, symbol, precision_amount):
    return {
        True: {
            "BTC/KRW": {
                0.1111: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "Purchase amount exceeds usable KRW"}, pronunciation=None)',
                0.11111: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "The number of coins can only be entered up to the fourth decimal point."}, pronunciation=None)',
            },
            "ETH/KRW": {
                0.1111: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "Purchase amount exceeds usable KRW"}, pronunciation=None)',
                0.11111: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "The number of coins can only be entered up to the fourth decimal point."}, pronunciation=None)',
            }
        },
        False: {
            "BTC/KRW": {
                0.1111: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "Order has exceeded available BTC"}, pronunciation=None)',
                0.11111: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "The number of coins can only be entered up to the fourth decimal point."}, pronunciation=None)',
            },
            "ETH/KRW": {
                0.1111: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "Order has exceeded the available ETH"}, pronunciation=None)',
                0.11111: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "The number of coins can only be entered up to the fourth decimal point."}, pronunciation=None)',
            }
        }
    }[is_buy][symbol][precision_amount]


def price_limit_results(is_buy, symbol, price):
    return {
        True: {
            "BTC/KRW": {
                0: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "The order price is $ 898,000 or more."}, pronunciation=None)',
                0.1: 'Translated(src=en, dest=en, text=bithumb {"status":"5500","message":"Invalid Parameter"}, pronunciation=bithumb {"status":"5500","message":"Invalid Parameter"})',
                1: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "You can trade in units of $ 1000."}, pronunciation=None)',
                1000: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "The order price is $ 898,000 or more."}, pronunciation=None)'
            },
            "ETH/KRW": {
                0: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "You can place an order for over 62,000 KRW."}, pronunciation=None)',
                0.1: 'Translated(src=en, dest=en, text=bithumb {"status":"5500","message":"Invalid Parameter"}, pronunciation=bithumb {"status":"5500","message":"Invalid Parameter"})',
                1: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "Can be traded in units of $ 500."}, pronunciation=None)',
                1000: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "You can place an order for over 62,000 KRW."}, pronunciation=None)'
            }
        },
        False: {
            "BTC/KRW": {
                0: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "The price is below the sellable amount."}, pronunciation=None)',
                0.1: 'Translated(src=en, dest=en, text=bithumb {"status":"5500","message":"Invalid Parameter"}, pronunciation=bithumb {"status":"5500","message":"Invalid Parameter"})',
                1: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "You can trade in units of $ 1000."}, pronunciation=None)',
                1000: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "The price is below the sellable amount."}, pronunciation=None)'
            },
            "ETH/KRW": {
                0: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "The price is below the sellable amount."}, pronunciation=None)',
                0.1: 'Translated(src=en, dest=en, text=bithumb {"status":"5500","message":"Invalid Parameter"}, pronunciation=bithumb {"status":"5500","message":"Invalid Parameter"})',
                1: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "Can be traded in units of $ 500."}, pronunciation=None)',
                1000: 'Translated(src=ko, dest=en, text=bithumb {"status": "5600", "message": "The price is below the sellable amount."}, pronunciation=None)'
            }
        }
    }[is_buy][symbol][price]
