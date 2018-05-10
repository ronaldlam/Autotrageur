from enum import Enum

import ccxt
import pytest

import bot.currencyconverter as currencyconverter
import bot.trader.ccxt_trader as ccxt_trader

# Namespace shortcuts.
CCXTTrader = ccxt_trader.CCXTTrader
xfail = pytest.mark.xfail

# Test Enums.
class OrderType(Enum):
    """An Enum for Order Types.

    Args:
        Enum (str): One of: 'buy' or 'sell'.
    """
    BUY = 'buy',
    SELL = 'sell'

# Test constants.
BTC_USD = 'BTC/USD'


class TestCCXTTraderInit:
    ext_exchanges = ['gemini', 'bithumb']

    @pytest.mark.parametrize('base, quote, exchange_name, slippage, target_amount,'
                            'exchange_config, dry_run', [
        ('BTC', 'USD', 'binance', 5.0, 50000, {}, False),
        ('BTC', 'USD', 'gemini', 5.0, 50000, {}, False),
        ('BTC', 'KRW', 'bithumb', 5.0, 50000, {}, False),
        ('BTC', 'USD', 'binance', 5.0, 50000, {}, True),
        ('BTC', 'USD', 'gemini', 5.0, 50000, {}, True),
        ('BTC', 'KRW', 'bithumb', 5.0, 50000, {}, True)
    ])
    def test_init_normal(self, base, quote, exchange_name, slippage, target_amount,
                         exchange_config, dry_run, mocker, ccxtfetcher_binance,
                         fake_ccxt_executor, fake_dryrun_executor):
        mocker.patch('bot.trader.ccxt_trader.CCXTFetcher', return_value=ccxtfetcher_binance)
        mocker.patch('bot.trader.ccxt_trader.CCXTExecutor', return_value=fake_ccxt_executor)
        mocker.patch('bot.trader.ccxt_trader.DryRunExecutor', return_value=fake_dryrun_executor)

        if exchange_name in self.ext_exchanges:
            exchange_obj = getattr(ccxt_trader.ccxt_extensions,
                ccxt_trader.EXTENSION_PREFIX + exchange_name)(exchange_config)
            mocker.patch.object(ccxt_trader.ccxt_extensions,
                ccxt_trader.EXTENSION_PREFIX + exchange_name,
                return_value=exchange_obj)
        else:
            exchange_obj = getattr(ccxt, exchange_name)(exchange_config)
            mocker.patch.object(ccxt, exchange_name, return_value=exchange_obj)

        trader = CCXTTrader(base, quote, exchange_name, slippage, target_amount,
                            exchange_config, dry_run)
        assert trader.base == base
        assert trader.quote == quote
        assert trader.exchange_name == exchange_name
        assert trader.slippage == slippage
        assert trader.target_amount == target_amount
        assert trader.ccxt_exchange is exchange_obj
        assert trader.fetcher is ccxtfetcher_binance

        if dry_run:
            assert trader.executor is fake_dryrun_executor
        else:
            assert trader.executor is fake_ccxt_executor


class TestCalcVolByBook:
    """For tests regarding ccxt_trader::_CCXTTrader__calc_vol_by_book."""

    @pytest.mark.parametrize('bids_or_asks, target_amount, final_volume', [
        # Good, one order, no overshoot.
        ([
            [10000.0, 2.0]
        ], 20000.0, 2.0),
        # Good, one order, negative overshoot.
        ([
            [11000.0, 2.0]
        ], 20000.0, 1.8181818181818181),
        # Good, two orders, negative overshoot.
        ([
            [10050.0, 1.0],
            [10000.0, 1.0]
        ], 20000.0, 1.995),
        # Good, multiple orders, larger numbers, larger negative overshoot.
        ([
            [20055.0, 1000.0],
            [15055.0, 3000.45],
            [10050.0, 1000.0],
            [10000.0, 50000.5]
        ], 100000000.0, 7472.772525),
        # Good, multiple orders, real case, negative overshoot.
        ([
            [756.87, 0.015191],
            [756.9, 0.017835],
            [756.91, 0.012548],
            [756.92, 0.011226],
            [756.93, 0.005943],
            [756.96, 0.007264],
            [756.97, 0.009905],
            [756.98, 0.011225],
            [756.99, 0.024437],
            [757.0, 3.172266],
            [757.54, 0.011219],
            [757.55, 0.02178],
            [757.56, 0.024418],
            [757.57, 0.007258],
            [757.58, 0.017818],
            [757.6, 0.91544843],
            [757.95, 0.005935],
            [757.96, 0.01649],
            [757.97, 0.01253],
            [757.98, 0.021766],
            [757.99, 10.5],
            [758.0, 100.0],
            [758.84, 0.02306],
            [758.85, 0.5],
            [758.98, 0.015796],
            [759.0, 100.0],
            [759.25, 112.9],
            [759.74, 9.4],
            [759.99, 0.6559],
            [760.0, 1.114685],
            [760.06, 0.015763],
            [760.14, 9.8],
            [760.27, 49.65],
            [760.46, 0.015162],
            [760.74, 0.181],
            [760.79, 0.015763],
            [760.88, 50.0],
            [760.91, 496.58],
            [761.54, 0.015727],
            [761.9, 1.25],
            [762.98, 0.015661],
            [763.36, 50.015692],
            [763.37, 58.0],
            [763.57, 16.0],
            [764.97, 0.015172],
            [765.13, 17.99],
            [765.31, 0.007],
            [765.32, 0.015141],
            [765.37, 54.98],
            [766.46, 0.15]
        ], 20000.0, 26.390243212957785)
    ])
    def test_calc_vol_by_book(self, mocker, fake_ccxt_trader, bids_or_asks, target_amount, final_volume):
        volume = fake_ccxt_trader._CCXTTrader__calc_vol_by_book(bids_or_asks, target_amount)
        assert volume == final_volume

    @pytest.mark.parametrize('bids_or_asks, target_amount', [
        # Not enough depth, one order.
        ([
            [10000.0, 1.0]
        ], 20000.0),
        # Not enough depth, two orders, minimal amounts.
        ([
            [10050.0, 0.001],
            [10000.0, 0.004]
        ], 20000.0),
        # Not enough depth, multiple orders, large numbers.
        ([
            [20055.0, 100.0],
            [15055.0, 300.45],
            [10050.0, 100.0],
            [10000.0, 500.5]
        ], 1000000000.12345678)
    ])
    def test_calc_vol_by_book_exception(self, mocker, fake_ccxt_trader, bids_or_asks, target_amount):
        with pytest.raises(ccxt_trader.OrderbookException):
            fake_ccxt_trader._CCXTTrader__calc_vol_by_book(bids_or_asks, target_amount)

class TestCheckExchangeLimits:
    """For tests regarding ccxt_trader::_CCXTTrader__check_exchange_limits."""

    def _internaltest_check_exchange_limits(self, mocker, fake_ccxt_trader, amount, price, markets):
        fake_ccxt_trader.ccxt_exchange.markets = {}
        mocker.patch.dict(fake_ccxt_trader.ccxt_exchange.markets, markets)
        fake_ccxt_trader._CCXTTrader__check_exchange_limits(amount, price)

        limits_dict = fake_ccxt_trader.ccxt_exchange.markets[BTC_USD]['limits']
        assert amount >= limits_dict['amount']['min']
        assert amount <= limits_dict['amount']['max']
        assert price >= limits_dict['price']['min']
        assert price <= limits_dict['price']['max']

    @pytest.mark.parametrize('amount, price', [
        (0.1, 0.9),
        (0.000000011, 0.00000009),
        (0.00000002, 0.99999999)
    ])
    @pytest.mark.parametrize('markets', [
        ({
            BTC_USD: {
                'limits': {
                    'amount': {
                        'min': 0,
                        'max': 1,
                    },
                    'price': {
                        'min': 0,
                        'max': 1,
                    }
                }
            }
        }),
        ({
            BTC_USD: {
                'limits': {
                    'amount': {
                        'min': 0.00000000,
                        'max': 1.99999999,
                    },
                    'price': {
                        'min': 0.00000000,
                        'max': 1.99999999,
                    }
                }
            }
        })
    ])
    def test_check_exchange_limits_small(self, mocker, fake_ccxt_trader, amount, price, markets):
        self._internaltest_check_exchange_limits(mocker, fake_ccxt_trader, amount, price, markets)

    @pytest.mark.parametrize('amount, price', [
        (10000001, 9999999),
        (99999991, 9999999),
        (10000000.00000000, 99999999.99999999)
    ])
    @pytest.mark.parametrize('markets', [
        ({
            BTC_USD: {
                'limits': {
                    'amount': {
                        'min': 10000000.00000000,
                        'max': 99999999.99999999,
                    },
                    'price': {
                        'min': 00000000.99999999,
                        'max': 99999999.99999999,
                    }
                }
            }
        })
    ])
    def test_check_exchange_limits_big(self, mocker, fake_ccxt_trader, amount, price, markets):
        self._internaltest_check_exchange_limits(mocker, fake_ccxt_trader, amount, price, markets)

    @pytest.mark.parametrize('amount, price', [
        (10000000.00000000, 00000000.99999998),
        (99999999.99999999, 00000000.99999998),
        (10000000.00000000, 1000000000),
        (99999999.99999999, 1000000000),
        (9999999.00000000, 00000000.99999999),
        (100000000.99999999, 00000000.99999999),
        (9999999.00000000, 99999999.99999999),
        (100000000.99999999, 99999999.99999999),
        (-100000000.99999999, 99999999.99999999),
        (100000000.99999999, -99999999.99999999),
    ])
    @pytest.mark.parametrize('markets', [
        ({
            BTC_USD: {
                'limits': {
                    'amount': {
                        'min': 10000000.00000000,
                        'max': 99999999.99999999,
                    },
                    'price': {
                        'min': 00000000.99999999,
                        'max': 99999999.99999999,
                    }
                }
            }
        })
    ])
    def test_check_exchange_limits_exception(self, mocker, fake_ccxt_trader, markets, amount, price):
        with pytest.raises(ccxt_trader.ExchangeLimitException):
            self._internaltest_check_exchange_limits(mocker, fake_ccxt_trader, amount, price, markets)


class TestRoundExchangePrecision:
    """Tests for ccxt_trader::_CCXTTrader__round_exchange_precision."""

    @pytest.mark.parametrize('precision, asset_amount, rounded_amount', [
        # Good, but 0 amount.
        ({
            BTC_USD: {
                'precision': {
                    'amount': 8
                }
            }
        }, 0, 0),
        # Good, 8 precision.
        ({
            BTC_USD: {
                'precision': {
                    'amount': 8
                }
            }
        }, 1.123456789, 1.12345679),
        # Good, 8 precision, large number.
        ({
            BTC_USD: {
                'precision': {
                    'amount': 8
                }
            }
        }, 10000000.123456789, 10000000.12345679),
        # Good, 8 precision, rounding with float ending in 5.
        ({
            BTC_USD: {
                'precision': {
                    'amount': 8
                }
            }
        }, 1.123456785, 1.12345678),    # NOTE: Does not round "up" to  1.12345679
        # Bad, 8 precision, typo, should remain unchanged.
        ({
            BTC_USD: {
                'precision': {
                    'amountt': 8
                }
            }
        }, 1.123456789, 1.123456789)
    ])
    @pytest.mark.parametrize('market_order', [True, 'emulated', False])
    def test_round_exchange_precision(self, mocker, fake_ccxt_trader, precision,
                                    market_order, asset_amount, rounded_amount):
        fake_ccxt_trader.ccxt_exchange.markets = {}
        mocker.patch.dict(fake_ccxt_trader.ccxt_exchange.markets, precision)
        result = fake_ccxt_trader._CCXTTrader__round_exchange_precision(
            market_order, BTC_USD, asset_amount)

        if market_order is True:
            assert result == rounded_amount
        else:
            assert result == asset_amount

    @pytest.mark.parametrize('precision, asset_amount, rounded_amount', [
        # Bad, no symbol, expect KeyError exception.
        pytest.param({
            'precision': {
                'amount': 8
            }
        }, 1.123456789, 1.123456789,
        marks=xfail(raises=KeyError, reason="Missing symbol key", strict=True)),
        # Bad, typo precision key, expect KeyError exception.
        pytest.param({
            BTC_USD: {
                'precisionn': {
                    'amount': 8
                }
            }
        }, 1.123456789, 1.123456789,
        marks=xfail(raises=KeyError, reason="Typo precision key", strict=True))
    ])
    def test_round_exchange_precision_bad(self, mocker, fake_ccxt_trader, precision,
                                          asset_amount, rounded_amount):
        market_order = True

        fake_ccxt_trader.ccxt_exchange.markets = {}
        mocker.patch.dict(fake_ccxt_trader.ccxt_exchange.markets, precision)
        result = fake_ccxt_trader._CCXTTrader__round_exchange_precision(
            market_order, BTC_USD, asset_amount)

        assert result == rounded_amount


class TestExecuteMarketOrder:
    """For tests regarding ccxt_trader::execute_market_buy and
       ccxt_trader::execute_market_sell."""

    fake_asset_price = 100.00
    fake_result = { 'fake': 'result' }
    fake_rounded_amount = 2.333
    fake_normal_market_order = { 'createMarketOrder': True }
    fake_emulated_market_order = { 'createMarketOrder': 'emulated' }

    def _asserts_for_market_order(self, mocker, fake_ccxt_trader, create_market_order, order_type):
        check_exchange_limits_params = [self.fake_rounded_amount, self.fake_asset_price]

        if order_type is OrderType.BUY:
            market_order_function = 'execute_market_buy'
            market_order_function_params = [self.fake_asset_price]
            round_exchange_precision_params = [create_market_order['createMarketOrder'], BTC_USD,
                (fake_ccxt_trader.target_amount / self.fake_asset_price)]

            if create_market_order == self.fake_normal_market_order:
                executor_function = 'create_market_buy_order'
                executor_function_params = [BTC_USD, self.fake_rounded_amount, self.fake_asset_price]
            else:
                executor_function = 'create_emulated_market_buy_order'
                executor_function_params = [BTC_USD, fake_ccxt_trader.target_amount, self.fake_asset_price,
                    fake_ccxt_trader.slippage]
        else:
            market_order_function = 'execute_market_sell'
            market_order_function_params = [self.fake_asset_price, self.fake_rounded_amount]
            round_exchange_precision_params = [create_market_order['createMarketOrder'], BTC_USD,
                self.fake_rounded_amount]

            if create_market_order == self.fake_normal_market_order:
                executor_function = 'create_market_sell_order'
                executor_function_params = [BTC_USD, self.fake_rounded_amount, self.fake_asset_price]
            else:
                executor_function = 'create_emulated_market_sell_order'
                executor_function_params = [BTC_USD, self.fake_asset_price, self.fake_rounded_amount,
                    fake_ccxt_trader.slippage]

        result = getattr(fake_ccxt_trader, market_order_function)(*market_order_function_params)
        fake_ccxt_trader._CCXTTrader__round_exchange_precision.assert_called_with(
            *round_exchange_precision_params)
        fake_ccxt_trader._CCXTTrader__check_exchange_limits.assert_called_with(
            *check_exchange_limits_params)

        if create_market_order == self.fake_normal_market_order:
            getattr(fake_ccxt_trader.executor, executor_function).assert_called_with(
                *executor_function_params)
            assert result == self.fake_result
        elif create_market_order == self.fake_emulated_market_order:
            getattr(fake_ccxt_trader.executor, executor_function).assert_called_with(
                *executor_function_params)
            assert result == self.fake_result
        else:
            # Should not reach here.
            pytest.fail('Unsupported market buy type')

    def _setup_mocks(self, mocker, fake_ccxt_trader, create_market_order, order_type):
        fake_ccxt_trader.ccxt_exchange.has = {}
        mocker.patch.dict(fake_ccxt_trader.ccxt_exchange.has, create_market_order)
        mocker.patch.object(fake_ccxt_trader, '_CCXTTrader__round_exchange_precision',
            return_value=self.fake_rounded_amount)
        mocker.patch.object(fake_ccxt_trader, '_CCXTTrader__check_exchange_limits')

        if order_type is OrderType.BUY:
            mocked_executor_function = (
                'create_market_buy_order' if create_market_order == self.fake_normal_market_order
                                          else 'create_emulated_market_buy_order')
        else:
            mocked_executor_function = (
                'create_market_sell_order' if create_market_order == self.fake_normal_market_order
                                          else 'create_emulated_market_sell_order')

        mocker.patch.object(fake_ccxt_trader.executor, mocked_executor_function,
            return_value=self.fake_result)

    @pytest.mark.parametrize('order_type', [ OrderType.BUY, OrderType.SELL ])
    @pytest.mark.parametrize('create_market_order', [
        { 'createMarketOrder': True },
        { 'createMarketOrder': 'emulated' }
    ])
    def test_execute_market_order_normal(self, mocker, fake_ccxt_trader, order_type, create_market_order):
        self._setup_mocks(mocker, fake_ccxt_trader, create_market_order, order_type)
        self._asserts_for_market_order(mocker, fake_ccxt_trader, create_market_order, order_type)

    @pytest.mark.parametrize('order_type', [ OrderType.BUY, OrderType.SELL ])
    @pytest.mark.parametrize('create_market_order', [
        { 'createMarketOrder': None },
        { 'createMarketOrder': 0 },
        { 'createMarketOrder': "" },
        { 'createMarketOrder': False }
    ])
    def test_execute_market_buy_exception(self, mocker, fake_ccxt_trader, order_type, create_market_order):
        with pytest.raises(NotImplementedError):
            self._setup_mocks(mocker, fake_ccxt_trader, create_market_order, order_type)
            fake_ccxt_trader.execute_market_buy(self.fake_asset_price)


@pytest.mark.parametrize('urls', [
    None,
    {},
    {
        'api': 'fake.url.com'
    },
    {
        'api': 'fake.url.com',
        'test': 'diff.url.ca'
    },
    {
        'api': 'fake.url.com',
        'test': 'fake.url.com'
    }
])
def test_connect_test_api(mocker, fake_ccxt_trader, urls):
    fake_ccxt_trader.ccxt_exchange.urls = urls
    exchange_urls = fake_ccxt_trader.ccxt_exchange.urls

    if exchange_urls is None:
        with pytest.raises(TypeError, message="NoneType object in urls dict"):
            fake_ccxt_trader.connect_test_api()
    elif exchange_urls.get('test') is None:
        with pytest.raises(NotImplementedError):
            fake_ccxt_trader.connect_test_api()
    else:
        fake_ccxt_trader.connect_test_api()
        assert exchange_urls['api'] == exchange_urls['test']


def test_check_wallet_balances(mocker, fake_ccxt_trader, symbols):
    mocker.patch.object(fake_ccxt_trader.fetcher, 'fetch_free_balance')
    fake_ccxt_trader.check_wallet_balances()
    assert fake_ccxt_trader.fetcher.fetch_free_balance.call_count == 2
    assert fake_ccxt_trader.fetcher.fetch_free_balance.call_args_list == (
        [mocker.call(symbols['bitcoin']), mocker.call(symbols['usd'])])


def test_get_full_orderbook(mocker, fake_ccxt_trader, symbols):
    mocker.patch.object(fake_ccxt_trader.fetcher, 'get_full_orderbook')
    fake_ccxt_trader.get_full_orderbook()
    assert fake_ccxt_trader.fetcher.get_full_orderbook.call_count == 1
    fake_ccxt_trader.fetcher.get_full_orderbook.assert_called_with(symbols['bitcoin'], symbols['usd'])


class TestGetAdjustedMarketPriceFromOrderbook:
    fake_bids_or_asks = [['fake', 'bids', 'asks']]
    fake_asset_volume = 10
    fake_target_amount = 100
    fake_usd_value = 150

    @pytest.mark.parametrize('conversion_needed', [
        True,
        False,
        None
    ])
    def test_get_adjusted_market_price_from_orderbook(self, mocker, fake_ccxt_trader,
                                                      conversion_needed):
        mocker.patch.object(fake_ccxt_trader, '_CCXTTrader__calc_vol_by_book',
            return_value=self.fake_asset_volume)
        asset_volume = fake_ccxt_trader._CCXTTrader__calc_vol_by_book.return_value

        mocker.patch.object(fake_ccxt_trader, 'target_amount', self.fake_target_amount)
        target_amount = fake_ccxt_trader.target_amount

        if conversion_needed:
            mocker.patch.object(ccxt_trader.currencyconverter, 'convert_currencies', return_value=self.fake_usd_value)
            mocker.patch.object(fake_ccxt_trader, 'conversion_needed', conversion_needed)

        market_price = fake_ccxt_trader.get_adjusted_market_price_from_orderbook(self.fake_bids_or_asks)

        if conversion_needed:
            asset_usd_value = ccxt_trader.currencyconverter.convert_currencies.return_value
            assert market_price == asset_usd_value / asset_volume
        else:
            assert market_price == target_amount / asset_volume


def test_load_markets(mocker, fake_ccxt_trader):
    mocker.patch.object(fake_ccxt_trader.ccxt_exchange, 'load_markets')
    fake_ccxt_trader.load_markets()
    assert fake_ccxt_trader.ccxt_exchange.load_markets.call_count == 1
    fake_ccxt_trader.ccxt_exchange.load_markets.assert_called_with()


@pytest.mark.parametrize('is_conv_needed', [ True, False, None ])
def test_set_conversion_needed(fake_ccxt_trader, is_conv_needed):
    fake_ccxt_trader.set_conversion_needed(is_conv_needed)
    if is_conv_needed:
        assert fake_ccxt_trader.conversion_needed == is_conv_needed