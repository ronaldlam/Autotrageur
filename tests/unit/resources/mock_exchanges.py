import ccxt
import pytest


@pytest.fixture()
def fake_binance(mocker):
    fake_binance_exchange = mocker.patch.object(ccxt, 'binance', autospec=True)

    # Fake exchange fees.
    fake_binance_exchange.fees = {
        'trading': {
            'maker': 0.25,
            'taker': 0.10
        }
    }

    # Fake account balances.
    fake_binance_exchange.balances = {
        'BTC': {
            'free': 1.50,
            'used': 0.00,
            'total': 1.50,
        },
        'USD': {
            'free': 123.00,
            'used': 456.00,
            'total': 579.00,
        }
    }
    return fake_binance_exchange
