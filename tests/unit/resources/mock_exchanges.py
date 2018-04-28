import ccxt
import pytest

@pytest.fixture()
def fake_generic_exchange(mocker):
    fake_exchange = mocker.patch.object(ccxt, 'Exchange', autospec=True)
    fake_exchange.fees = {
        'trading': {
            'maker': 0.25
        }
    }
    return fake_exchange

@pytest.fixture()
def fake_binance(mocker):
    fake_binance_exchange = mocker.patch.object(ccxt, 'binance', autospec=True)
    fake_binance_exchange.fees = {
        'trading': {
            'maker': 0.25
        }
    }
    return fake_binance_exchange