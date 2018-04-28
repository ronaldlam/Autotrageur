import ccxt
import pytest
# from pytest_mock import mocker

from tests.unit.resources.mock_exchanges import (
    fake_binance,
    fake_generic_exchange)
from libs.trade.fetcher.ccxt_fetcher import CCXTFetcher

bad_fee_structures = [
    {},
    {
        'trading': {
            'maker': 0.25
        }
    },
    {
        'trading': {
            'maker': 0.25,
            'taker': 0.10
        }
    },
    {
        'garbage': {
            'maker': 0.25,
            'taker': 0.10
        }
    }
]


@pytest.fixture()
def ccxtfetcher_binance(fake_binance):
    return CCXTFetcher(fake_binance)

@pytest.fixture(params=bad_fee_structures)
def ccxtfetcher_binance_bad_fees(fake_binance, request):
    fake_binance.fees =
    return CCXTFetcher(fake_binance)

@pytest.mark.parametrize('exchange', [
    ccxt.binance(),
    pytest.param("binance", marks=pytest.mark.xfail(raises=TypeError, reason="string not ccxt object", strict=True)),
    pytest.param("", marks=pytest.mark.xfail(raises=TypeError, reason="empty string not ccxt object", strict=True)),
    pytest.param(None, marks=pytest.mark.xfail(raises=TypeError, reason="None not ccxt object", strict=True)),
])
def test_init(exchange):
    fetcher = CCXTFetcher(exchange)
    assert fetcher.exchange == exchange


@pytest.mark.parametrize('ccxt_fetcher', [
    ccxtfetcher_binance
])
def test_fetch_maker_fees(ccxt_fetcher):
    maker_fees = ccxt_fetcher.fetch_maker_fees()
    assert maker_fees == 0.25

# def test_fetch_maker_fees_full(ccxtfetcher_binance):
#     maker_fees = ccxtfetcher_binance.fetch_maker_fees()
#     assert maker_fees == 0.25

# def test_fetch_maker_fees_feeless(mocker, ccxtfetcher_binance):
#     mocker.patch.object(ccxtfetcher_binance, 'fees', {})
#     maker_fees = ccxtfetcher_binance.fetch_maker_fees()
#     assert maker_fees == 0.25