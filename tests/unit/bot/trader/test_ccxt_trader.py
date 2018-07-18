from enum import Enum
from decimal import Decimal

import ccxt
import pytest

import bot.currencyconverter as currencyconverter
import bot.trader.ccxt_trader as ccxt_trader
from libs.fiat_symbols import FIAT_SYMBOLS
from libs.utilities import set_autotrageur_decimal_context, num_to_decimal

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
FAKE_FOREX_RATIO = num_to_decimal(1000)
set_autotrageur_decimal_context()


class TestCCXTTraderInit:
    ext_exchanges = ['gemini', 'bithumb']

    @pytest.mark.parametrize('base, quote, exchange_name, slippage, quote_target_amount,'
                            'exchange_config, dry_run', [
        ('BTC', 'USD', 'binance', Decimal('5.0'), Decimal('50000'), {}, False),
        ('BTC', 'USD', 'gemini', Decimal('5.0'), Decimal('50000'), {}, False),
        ('BTC', 'KRW', 'bithumb', Decimal('5.0'), Decimal('50000'), {}, False),
        ('BTC', 'USD', 'binance', Decimal('5.0'), Decimal('50000'), {}, True),
        ('BTC', 'USD', 'gemini', Decimal('5.0'), Decimal('50000'), {}, True),
        ('BTC', 'KRW', 'bithumb', Decimal('5.0'), Decimal('50000'), {}, True)
    ])
    def test_init_normal(self, base, quote, exchange_name, slippage, quote_target_amount,
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

        trader = CCXTTrader(base, quote, exchange_name, slippage,
                            exchange_config, dry_run)
        assert trader.base == base
        assert trader.quote == quote
        assert trader.exchange_name == exchange_name
        assert trader.slippage == slippage
        assert trader.ccxt_exchange is exchange_obj
        assert trader.fetcher is ccxtfetcher_binance

        # Initialized variables not from config.
        assert trader.quote_target_amount == num_to_decimal(0.0)
        assert trader.usd_target_amount == num_to_decimal(0.0)
        assert trader.conversion_needed is False
        assert trader.forex_ratio is None

        if dry_run:
            assert trader.executor is fake_dryrun_executor
        else:
            assert trader.executor is fake_ccxt_executor


class TestCalcVolByBook:
    """For tests regarding ccxt_trader::_CCXTTrader__calc_vol_by_book."""

    @pytest.mark.parametrize('bids_or_asks, quote_target_amount, final_volume', [
        # Good, one order, no overshoot.
        ([
            [10000.0, 2.0]
        ], Decimal('20000.0'), Decimal('2.0')),
        # Good, one order, negative overshoot.
        ([
            [11000.0, 2.0]
        ], Decimal('20000.0'), Decimal('1.818181818181818181818181818')),
        # Good, two orders, negative overshoot.
        ([
            [10050.0, 1.0],
            [10000.0, 1.0]
        ], Decimal('20000.0'), Decimal('1.995')),
        # Good, multiple orders, larger numbers, larger negative overshoot.
        ([
            [20055.0, 1000.0],
            [15055.0, 3000.45],
            [10050.0, 1000.0],
            [10000.0, 50000.5]
        ], Decimal('100000000.0'), Decimal('7472.772525')),
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
        ], Decimal('20000.0'), Decimal('26.39024321295778364116094987'))
    ])
    def test_calc_vol_by_book(self, mocker, fake_ccxt_trader, bids_or_asks, quote_target_amount, final_volume):
        volume = fake_ccxt_trader._CCXTTrader__calc_vol_by_book(bids_or_asks, quote_target_amount)
        assert volume == final_volume

    @pytest.mark.parametrize('bids_or_asks, quote_target_amount', [
        # Not enough depth, one order.
        ([
            [10000.0, 1.0]
        ], Decimal('20000.0')),
        # Not enough depth, two orders, minimal amounts.
        ([
            [10050.0, 0.001],
            [10000.0, 0.004]
        ], Decimal('20000.0')),
        # Not enough depth, multiple orders, large numbers.
        ([
            [20055.0, 100.0],
            [15055.0, 300.45],
            [10050.0, 100.0],
            [10000.0, 500.5]
        ], Decimal('1000000000.12345678'))
    ])
    def test_calc_vol_by_book_exception(self, mocker, fake_ccxt_trader, bids_or_asks, quote_target_amount):
        with pytest.raises(ccxt_trader.OrderbookException):
            fake_ccxt_trader._CCXTTrader__calc_vol_by_book(bids_or_asks, quote_target_amount)

class TestCheckExchangeLimits:
    """For tests regarding ccxt_trader::_CCXTTrader__check_exchange_limits."""

    def _internaltest_check_exchange_limits(self, mocker, fake_ccxt_trader, amount, price, markets):
        fake_ccxt_trader.ccxt_exchange.markets = {}
        mocker.patch.dict(fake_ccxt_trader.ccxt_exchange.markets, markets)
        fake_ccxt_trader._CCXTTrader__check_exchange_limits(amount, price)

        limits_dict = fake_ccxt_trader.ccxt_exchange.markets[BTC_USD]['limits']
        assert amount >= num_to_decimal(limits_dict['amount']['min'])
        assert amount <= num_to_decimal(limits_dict['amount']['max'])
        assert price >= num_to_decimal(limits_dict['price']['min'])
        assert price <= num_to_decimal(limits_dict['price']['max'])

    @pytest.mark.parametrize('amount, price', [
        (Decimal('0.1'), Decimal('0.9')),
        (Decimal('0.000000011'), Decimal('0.00000009')),
        (Decimal('0.00000002'), Decimal('0.99999999'))
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
        (Decimal('10000001'), Decimal('9999999')),
        (Decimal('99999991'), Decimal('9999999')),
        (Decimal('10000000.00000000'), Decimal('99999999.99999999'))
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

    @pytest.mark.parametrize('amount, price, measure, limit_type', [
        (Decimal('10000000.00000000'), Decimal('00000000.99999998'), 'price', 'min'),
        (Decimal('99999999.99999999'), Decimal('00000000.99999998'), 'price', 'min'),
        (Decimal('10000000.00000000'), Decimal('1000000000'), 'price', 'max'),
        (Decimal('99999999.99999999'), Decimal('1000000000'), 'price', 'max'),
        (Decimal('9999999.00000000'), Decimal('00000000.99999999'), 'amount', 'min'),
        (Decimal('100000000.99999999'), Decimal('00000000.99999999'), 'amount', 'max'),
        (Decimal('9999999.00000000'), Decimal('99999999.99999999'), 'amount', 'min'),
        (Decimal('100000000.99999999'), Decimal('99999999.99999999'), 'amount', 'max'),
        (Decimal('-100000000.99999999'), Decimal('99999999.99999999'), 'amount', 'min'),
        (Decimal('100000000.99999999'), Decimal('-99999999.99999999'), 'amount', 'max'),
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
    def test_check_exchange_limits_exception(self, mocker, fake_ccxt_trader,
                                             markets, amount, price, measure,
                                             limit_type):
        with pytest.raises(ccxt_trader.ExchangeLimitException) as e:
            self._internaltest_check_exchange_limits(mocker, fake_ccxt_trader,
                amount, price, markets)
        assert e.type == ccxt_trader.ExchangeLimitException

        comparison_op = 'less' if limit_type is 'min' else 'more'
        if measure == 'amount':
            assert str(e.value) ==  (
                "Order {} {} {} {} than exchange limit {} {}.".format(measure,
                    amount, fake_ccxt_trader.base, comparison_op,
                    markets[BTC_USD]['limits'][measure][limit_type],
                    fake_ccxt_trader.base))
        else:
            assert str(e.value) ==  (
                "Order {} {} {} {} than exchange limit {} {}.".format(measure,
                    price, fake_ccxt_trader.base, comparison_op,
                    markets[BTC_USD]['limits'][measure][limit_type],
                    fake_ccxt_trader.base))


class TestRoundExchangePrecisionPrivate:
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
        }, Decimal('1.123456789'), Decimal('1.12345678')),
        # Good, 8 precision, large number.
        ({
            BTC_USD: {
                'precision': {
                    'amount': 8
                }
            }
        }, Decimal('10000000.123456789'), Decimal('10000000.12345678')),
        # Good, 8 precision, rounding with float ending in 5.
        ({
            BTC_USD: {
                'precision': {
                    'amount': 8
                }
            }
        }, Decimal('1.123456785'), Decimal('1.12345678')),    # NOTE: Does not round "up" to  1.12345679
        # Bad, 8 precision, typo, should remain unchanged.
        ({
            BTC_USD: {
                'precision': {
                    'amountt': 8
                }
            }
        }, Decimal('1.123456789'), Decimal('1.123456789'))
    ])
    @pytest.mark.parametrize('market_order', [True, 'emulated', False])
    def test_round_exchange_precision_private(self, mocker, fake_ccxt_trader, precision,
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
        }, Decimal('1.123456789'), Decimal('1.123456789'),
        marks=xfail(raises=KeyError, reason="Missing symbol key", strict=True)),
        # Bad, typo precision key, expect KeyError exception.
        pytest.param({
            BTC_USD: {
                'precisionn': {
                    'amount': 8
                }
            }
        }, Decimal('1.123456789'), Decimal('1.123456789'),
        marks=xfail(raises=KeyError, reason="Typo precision key", strict=True))
    ])
    def test_round_exchange_precision_private_bad(self, mocker, fake_ccxt_trader,
                                                  precision, asset_amount, rounded_amount):
        market_order = True

        fake_ccxt_trader.ccxt_exchange.markets = {}
        mocker.patch.dict(fake_ccxt_trader.ccxt_exchange.markets, precision)
        result = fake_ccxt_trader._CCXTTrader__round_exchange_precision(
            market_order, BTC_USD, asset_amount)

        assert result == rounded_amount


class TestExecuteMarketOrder:
    """For tests regarding ccxt_trader::execute_market_buy and
       ccxt_trader::execute_market_sell."""

    fake_asset_price = Decimal('100.00')
    fake_quote_target = Decimal('1000')
    fake_result = { 'fake': 'result' }
    fake_rounded_amount = Decimal('2.333')
    fake_normal_market_order = { 'createMarketOrder': True }
    fake_emulated_market_order = { 'createMarketOrder': 'emulated' }

    def _asserts_for_market_order(self, mocker, fake_ccxt_trader, create_market_order, order_type):
        check_exchange_limits_params = [self.fake_rounded_amount, self.fake_asset_price]

        if order_type is OrderType.BUY:
            market_order_function = 'execute_market_buy'
            market_order_function_params = [self.fake_asset_price]
            fake_asset_amount = fake_ccxt_trader.quote_target_amount / self.fake_asset_price
            fake_quote_target_amount = fake_ccxt_trader.quote_target_amount
            if fake_ccxt_trader.ccxt_exchange.buy_target_includes_fee is False:
                fee_ratio = Decimal('1') + fake_ccxt_trader.get_taker_fee()
                fake_asset_amount /= fee_ratio
                fake_quote_target_amount /= fee_ratio
            round_exchange_precision_params = [
                create_market_order['createMarketOrder'],
                BTC_USD,
                fake_asset_amount
            ]

            if create_market_order == self.fake_normal_market_order:
                executor_function = 'create_market_buy_order'
                executor_function_params = [BTC_USD, self.fake_rounded_amount, self.fake_asset_price]
            else:
                executor_function = 'create_emulated_market_buy_order'
                executor_function_params = [BTC_USD, fake_quote_target_amount, self.fake_asset_price,
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

    def _setup_mocks(self, mocker, fake_ccxt_trader, buy_target_includes_fee,
                     fee, create_market_order, order_type):
        if buy_target_includes_fee is not None:
            mocker.patch.object(fake_ccxt_trader.ccxt_exchange,
                                'buy_target_includes_fee',
                                buy_target_includes_fee,
                                create=True)
            mocker.patch.object(fake_ccxt_trader,
                                'get_taker_fee', return_value=fee)
        mocker.patch.object(
            fake_ccxt_trader, 'quote_target_amount', self.fake_quote_target)
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

    @pytest.mark.parametrize('buy_target_includes_fee', [True, False])
    @pytest.mark.parametrize('fee', [Decimal('0'), Decimal('0.01')])
    @pytest.mark.parametrize('order_type', [ OrderType.BUY, OrderType.SELL ])
    @pytest.mark.parametrize('create_market_order', [
        { 'createMarketOrder': True },
        { 'createMarketOrder': 'emulated' }
    ])
    def test_execute_market_order_normal(self, mocker, fake_ccxt_trader,
                                         buy_target_includes_fee, fee,
                                         order_type, create_market_order):
        self._setup_mocks(mocker, fake_ccxt_trader, buy_target_includes_fee,
                          fee, create_market_order, order_type)
        self._asserts_for_market_order(mocker, fake_ccxt_trader,
                                       create_market_order, order_type)

    @pytest.mark.parametrize('buy_target_includes_fee', [True, False, None])
    @pytest.mark.parametrize('order_type', [ OrderType.BUY, OrderType.SELL ])
    @pytest.mark.parametrize('create_market_order', [
        { 'createMarketOrder': None },
        { 'createMarketOrder': 0 },
        { 'createMarketOrder': "" },
        { 'createMarketOrder': False }
    ])
    def test_execute_market_buy_exception(self, mocker, fake_ccxt_trader,
                                          buy_target_includes_fee, order_type,
                                          create_market_order):
        with pytest.raises((NotImplementedError, AttributeError)):
            mock_fee = 0
            self._setup_mocks(mocker, fake_ccxt_trader,
                              buy_target_includes_fee, mock_fee,
                              create_market_order, order_type)
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


def test_get_full_orderbook(mocker, fake_ccxt_trader, symbols):
    mocker.patch.object(fake_ccxt_trader.fetcher, 'get_full_orderbook')
    fake_ccxt_trader.get_full_orderbook()
    assert fake_ccxt_trader.fetcher.get_full_orderbook.call_count == 1
    fake_ccxt_trader.fetcher.get_full_orderbook.assert_called_with(symbols['bitcoin'], symbols['usd'])


@pytest.mark.parametrize('limit, expected_result', [
    (0.02, Decimal('0.02')),
    (0, Decimal('0')),
    (1, Decimal('1')),
    (1234569, Decimal('1234569')),
    (None, None)
])
def test_get_min_base_limit(mocker, fake_ccxt_trader, limit, expected_result):
    fake_markets = {
        '{}/{}'.format(fake_ccxt_trader.base, fake_ccxt_trader.quote): {
            'limits': {
                'amount': {
                    "min": limit
                }
            }
        }
    }
    mocker.patch.object(fake_ccxt_trader.ccxt_exchange, "markets", fake_markets)

    result = fake_ccxt_trader.get_min_base_limit()

    assert result == expected_result


class TestGetAdjustedMarketPriceFromOrderbook:
    fake_bids_or_asks = [['fake', 'bids', 'asks']]
    fake_quote_target_amount = Decimal('100')
    fake_usd_target_amount = Decimal('150')

    @pytest.mark.parametrize(
        'usd_target_amount, quote_target_amount, asset_volume, result_usd_price, result_quote_price', [
            (Decimal('100'), Decimal('100'), Decimal('5'), Decimal('20'), Decimal('20')),
            (Decimal('100000'), Decimal('100'), Decimal('5'), Decimal('20000'), Decimal('20')),
            (Decimal('100'), Decimal('100000'), Decimal('5'), Decimal('20'), Decimal('20000'))
    ])
    def test_get_prices_from_orderbook(self, mocker, fake_ccxt_trader,
                                       usd_target_amount, quote_target_amount,
                                       asset_volume, result_usd_price,
                                       result_quote_price):
        mocker.patch.object(fake_ccxt_trader, 'usd_target_amount',
                            usd_target_amount)
        mocker.patch.object(fake_ccxt_trader, 'quote_target_amount',
                            quote_target_amount)
        calc_vol = mocker.patch.object(fake_ccxt_trader,
                                       '_CCXTTrader__calc_vol_by_book',
                                       return_value=asset_volume)

        usd_price, quote_price = fake_ccxt_trader.get_prices_from_orderbook(
            self.fake_bids_or_asks)

        calc_vol.assert_called_once_with(
            self.fake_bids_or_asks, quote_target_amount)
        assert usd_price == result_usd_price
        assert quote_price == result_quote_price

    @pytest.mark.parametrize('orderbook_exception', [True, False])
    def test_get_prices_from_orderbook_exception(self, mocker, fake_ccxt_trader, orderbook_exception):
        calc_volume = mocker.patch.object(fake_ccxt_trader,
                                          '_CCXTTrader__calc_vol_by_book',
                                          return_value=Decimal('0'))
        mocker.patch.object(fake_ccxt_trader, 'usd_target_amount',
                            self.fake_usd_target_amount)
        mocker.patch.object(fake_ccxt_trader, 'quote_target_amount',
                            self.fake_quote_target_amount)

        if orderbook_exception:
            calc_volume.side_effect = ccxt_trader.OrderbookException
            with pytest.raises(ccxt_trader.OrderbookException):
                fake_ccxt_trader.get_prices_from_orderbook(
                    self.fake_bids_or_asks)
        else:
            with pytest.raises(ZeroDivisionError):
                fake_ccxt_trader.get_prices_from_orderbook(
                    self.fake_bids_or_asks)


def test_load_markets(mocker, fake_ccxt_trader):
    mocker.patch.object(fake_ccxt_trader.ccxt_exchange, 'load_markets')
    fake_ccxt_trader.load_markets()
    assert fake_ccxt_trader.ccxt_exchange.load_markets.call_count == 1
    fake_ccxt_trader.ccxt_exchange.load_markets.assert_called_with()


def test_get_taker_fee(mocker, fake_ccxt_trader):
    mocker.patch.object(fake_ccxt_trader.fetcher, 'fetch_taker_fees')
    fake_ccxt_trader.get_taker_fee()
    fake_ccxt_trader.fetcher.fetch_taker_fees.assert_called_with()


def test_round_exchange_precision_public(mocker, fake_ccxt_trader):
    FAKE_AMOUNT_TO_ROUND = num_to_decimal(9999.99)
    mocker.patch.object(fake_ccxt_trader, '_CCXTTrader__round_exchange_precision')
    fake_ccxt_trader.round_exchange_precision(FAKE_AMOUNT_TO_ROUND)
    fake_ccxt_trader._CCXTTrader__round_exchange_precision.assert_called_once_with(
        True, 'BTC/USD', FAKE_AMOUNT_TO_ROUND)


@pytest.mark.parametrize('forex_quote', [
    'KRW',
    'JPY',
    'CAD',
    'USD',
    'BTC',
    'ETH',
    'RONCOIN',
    'DREWCOIN'
])
def test_set_forex_ratio(mocker, fake_ccxt_trader, forex_quote):
    is_forex = False

    if forex_quote in FIAT_SYMBOLS:
        is_forex = True
        mocker.patch.object(ccxt_trader.currencyconverter, 'convert_currencies', return_value=FAKE_FOREX_RATIO)
    else:
        mocker.patch.object(ccxt_trader.currencyconverter, 'convert_currencies', return_value=None)

    mocker.patch.object(fake_ccxt_trader, 'quote', forex_quote)
    fake_ccxt_trader.set_forex_ratio()

    if is_forex:
        assert fake_ccxt_trader.forex_ratio is FAKE_FOREX_RATIO
    else:
        assert fake_ccxt_trader.forex_ratio is None


class TestSetTargetAmount:
    fake_target_amount = Decimal('1234')

    @pytest.mark.parametrize(
        'target_amount, is_usd, conversion_needed, result_usd, result_quote', [
            (Decimal('1000'), True, False, Decimal('1000'), Decimal('1000')),
            (Decimal('1000'), False, False, Decimal('1000'), Decimal('1000')),
            (Decimal('1'), True, True, Decimal('1'), Decimal('1000')),
            (Decimal('1000'), False, True, Decimal('1'), Decimal('1000')),
            (Decimal('0'), True, False, Decimal('0'), Decimal('0')),
            (Decimal('0'), False, False, Decimal('0'), Decimal('0')),
            (Decimal('0'), True, True, Decimal('0'), Decimal('0')),
            (Decimal('0'), False, True, Decimal('0'), Decimal('0')),
    ])
    def test_set_target_amount(self, mocker, fake_ccxt_trader, target_amount, is_usd, conversion_needed, result_usd, result_quote):
        mocker.patch.object(fake_ccxt_trader, 'forex_ratio', FAKE_FOREX_RATIO)
        mocker.patch.object(fake_ccxt_trader, 'conversion_needed', conversion_needed)

        fake_ccxt_trader.set_target_amounts(target_amount, is_usd)

        assert fake_ccxt_trader.usd_target_amount == result_usd
        assert fake_ccxt_trader.quote_target_amount == result_quote

    @pytest.mark.parametrize('is_usd', [True, False])
    def test_set_target_amount_no_forex_quote(self, mocker, fake_ccxt_trader, is_usd):
        mocker.patch.object(fake_ccxt_trader, 'forex_ratio', None)
        mocker.patch.object(fake_ccxt_trader, 'conversion_needed', True)
        with pytest.raises(ccxt_trader.NoForexQuoteException):
            fake_ccxt_trader.set_target_amounts(self.fake_target_amount, is_usd)

    def test_set_target_amount_bad_forex_quote(self, mocker, fake_ccxt_trader):
        mocker.patch.object(fake_ccxt_trader, 'forex_ratio', Decimal('0'))
        mocker.patch.object(fake_ccxt_trader, 'conversion_needed', True)
        with pytest.raises(ZeroDivisionError):
            fake_ccxt_trader.set_target_amounts(self.fake_target_amount, False)


@pytest.mark.parametrize('live_balances, dryrun_balances, conversion_needed, is_dry_run, result_usd_bal', [
    ((Decimal('1'), Decimal('1000')), (Decimal('2'), Decimal('2000')), True, True, Decimal('2')),
    ((Decimal('1'), Decimal('1000')), (Decimal('2'), Decimal('2000')), True, False, Decimal('1')),
    ((Decimal('1'), Decimal('1000')), (Decimal('2'), Decimal('2000')), False, True, Decimal('2000')),
    ((Decimal('1'), Decimal('1000')), (Decimal('2'), Decimal('2000')), False, False, Decimal('1000')),
])
def test_update_wallet_balances(mocker, fake_ccxt_trader, symbols, live_balances, dryrun_balances, conversion_needed, is_dry_run, result_usd_bal):
    mocker.patch.object(fake_ccxt_trader.fetcher, 'fetch_free_balances', return_value=live_balances)
    executor = mocker.patch.object(fake_ccxt_trader, 'executor')
    dry_run_exchange = mocker.patch.object(executor, 'dry_run_exchange')
    mocker.patch.object(dry_run_exchange, 'base_balance', dryrun_balances[0])
    mocker.patch.object(dry_run_exchange, 'quote_balance', dryrun_balances[1])
    mocker.patch.object(fake_ccxt_trader, 'conversion_needed', conversion_needed)
    mocker.patch.object(fake_ccxt_trader, 'forex_ratio', FAKE_FOREX_RATIO)

    fake_ccxt_trader.update_wallet_balances(is_dry_run=is_dry_run)

    assert fake_ccxt_trader.usd_bal == result_usd_bal
    if is_dry_run:
        assert fake_ccxt_trader.base_bal == dryrun_balances[0]
        assert fake_ccxt_trader.quote_bal == dryrun_balances[1]
    else:
        assert fake_ccxt_trader.base_bal == live_balances[0]
        assert fake_ccxt_trader.quote_bal == live_balances[1]
        fake_ccxt_trader.fetcher.fetch_free_balances.assert_called_once_with(symbols['bitcoin'], symbols['usd'])
