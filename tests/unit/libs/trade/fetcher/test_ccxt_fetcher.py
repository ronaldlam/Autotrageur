from decimal import Decimal

import ccxt
import pytest

from libs.trade.fetcher.ccxt_fetcher import CCXTFetcher


xfail = pytest.mark.xfail


# Test constants.
MAKER_FEE = Decimal('0.25')
TAKER_FEE = Decimal('0.10')
BTC_FREE_BALANCE = Decimal('1.50')
USD_FREE_BALANCE = Decimal('123.00')
BTC_LAST = 120.00


fee_structures = {
    'none': None,
    'empty': {},
    'no_trading':  {
        'garbage': {
            'maker': MAKER_FEE,
            'taker': TAKER_FEE
        }
    },
    'maker_only': {
        'trading': {
            'maker': MAKER_FEE
        }
    },
    'taker_only': {
        'trading': {
            'taker': TAKER_FEE
        }
    },
    'full': {
        'trading': {
            'maker': MAKER_FEE,
            'taker': TAKER_FEE
        }
    }
}

balance_structures = {
    'none': None,
    'empty': {},
    'no_free': {
        'BTC': {
            'used': 0.00,
            'total': 1.50,
        },
        'USD': {
            'used': 456.00,
            'total': 579.00,
        }
    },
    'full': {
        'BTC': {
            'free': BTC_FREE_BALANCE,
            'used': 0.00,
            'total': 1.50,
        },
        'USD': {
            'free': USD_FREE_BALANCE,
            'used': 456.00,
            'total': 579.00,
        }
    }
}

last_structures = {
    'none': None,
    'empty': {},
    'no_last': {
        'symbol': 'BTC/USD',
        'vwap': 123.00,
        'open': 122.00,
        'close': 121.00
    },
    'full': {
        'symbol': 'BTC/USD',
        'vwap': 123.00,
        'open': 122.00,
        'close': 121.00,
        'last': BTC_LAST
    }
}


@pytest.mark.parametrize('exchange', [
    ccxt.binance(),
    pytest.param("binance", marks=xfail(raises=TypeError, reason="string not ccxt object", strict=True)),
    pytest.param("", marks=xfail(raises=TypeError, reason="empty string not ccxt object", strict=True)),
    pytest.param(None, marks=xfail(raises=TypeError, reason="None not ccxt object", strict=True)),
])
def test_init(exchange):
    fetcher = CCXTFetcher(exchange)
    assert fetcher.exchange == exchange


@pytest.mark.parametrize('fee_structure_key, maker_fee', [
    pytest.param('none', MAKER_FEE, marks=xfail(raises=TypeError, reason="NoneType object is not subscriptable", strict=True)),
    pytest.param('empty', MAKER_FEE, marks=xfail(raises=KeyError, reason="No keys in empty dict", strict=True)),
    pytest.param('no_trading', MAKER_FEE, marks=xfail(raises=KeyError, reason="No trading key", strict=True)),
    pytest.param('taker_only', MAKER_FEE, marks=xfail(raises=KeyError, reason="No maker key", strict=True)),
    ('maker_only', MAKER_FEE),
    ('full', MAKER_FEE)
])
def test_fetch_maker_fees(mocker, ccxtfetcher_binance, fee_structure_key, maker_fee):
    mocker.patch.object(ccxtfetcher_binance.exchange, 'fees', fee_structures[fee_structure_key])
    maker_fees = ccxtfetcher_binance.fetch_maker_fees()
    assert type(maker_fees) is Decimal
    assert maker_fees == MAKER_FEE


@pytest.mark.parametrize('fee_structure_key, taker_fee', [
    pytest.param('none', TAKER_FEE, marks=xfail(raises=TypeError, reason="NoneType object is not subscriptable", strict=True)),
    pytest.param('empty', TAKER_FEE, marks=xfail(raises=KeyError, reason="No keys in empty dict", strict=True)),
    pytest.param('no_trading', TAKER_FEE, marks=xfail(raises=KeyError, reason="No trading key", strict=True)),
    pytest.param('maker_only', TAKER_FEE, marks=xfail(raises=KeyError, reason="No taker key", strict=True)),
    ('taker_only', TAKER_FEE),
    ('full', TAKER_FEE)
])
def test_fetch_taker_fees(mocker, ccxtfetcher_binance, fee_structure_key, taker_fee):
    mocker.patch.object(ccxtfetcher_binance.exchange, 'fees', fee_structures[fee_structure_key])
    taker_fees = ccxtfetcher_binance.fetch_taker_fees()
    assert type(taker_fees) is Decimal
    assert taker_fees == TAKER_FEE


@pytest.mark.parametrize('base, quote, balance_structure_key, base_free_balance, quote_free_balance', [
    pytest.param('BTC', 'USD', 'none', BTC_FREE_BALANCE, USD_FREE_BALANCE, marks=xfail(raises=TypeError, reason="NoneType object is not subscriptable", strict=True)),
    pytest.param('BTC', 'USD', 'empty', BTC_FREE_BALANCE, USD_FREE_BALANCE, marks=xfail(raises=KeyError, reason="No keys in empty dict", strict=True)),
    pytest.param('BTC', 'USD', 'no_free', BTC_FREE_BALANCE, USD_FREE_BALANCE, marks=xfail(raises=KeyError, reason="No free key", strict=True)),
    ('BTC', 'USD', 'full', BTC_FREE_BALANCE, USD_FREE_BALANCE)
])
def test_fetch_free_balances(mocker, base, quote, balance_structure_key,
                             base_free_balance, quote_free_balance, ccxtfetcher_binance):
    mocker.patch.object(ccxtfetcher_binance.exchange, 'fetch_balance', return_value=balance_structures[balance_structure_key])
    (btc_balance, usd_balance) = ccxtfetcher_binance.fetch_free_balances(base, quote)
    ccxtfetcher_binance.exchange.fetch_balance.assert_called_once_with()
    assert type(btc_balance) is Decimal
    assert type(usd_balance) is Decimal
    assert (btc_balance, usd_balance) == (base_free_balance, quote_free_balance)


@pytest.mark.parametrize('base, quote', [
    pytest.param(None, None, marks=xfail(raises=TypeError, reason="Cannot append NoneType to NoneType", strict=True)),
    pytest.param(None, 'USD', marks=xfail(raises=TypeError, reason="Cannot append NoneType to str", strict=True)),
    pytest.param('BTC', None, marks=xfail(raises=TypeError, reason="Cannot append NoneType to str", strict=True)),
    ('BTC', ''),
    ('', 'BTC'),
    ('BTC', 'USD')
])
def test_get_full_orderbook(mocker, ccxtfetcher_binance, base, quote):
    mocker.patch.object(ccxtfetcher_binance.exchange, 'fetch_order_book')
    ccxtfetcher_binance.get_full_orderbook(base, quote)
    ccxtfetcher_binance.exchange.fetch_order_book.assert_called_once_with(base + '/' + quote)
