from decimal import Decimal
from unittest.mock import PropertyMock

import pytest

from bot.common.decimal_constants import ONE
from libs.utilities import split_symbol
import libs.ccxt_extensions as ccxt_extensions
from libs.trade.executor.dryrun_executor import (BUY_SIDE,
                                                 ORDER_TYPE_LIMIT,
                                                 ORDER_TYPE_MARKET, SELL_SIDE,
                                                 DryRunExecutor)


@pytest.fixture(scope="module")
def exchange():
    return ccxt_extensions.ext_gemini()


@pytest.fixture(scope="function")
def executor(mocker, exchange):
    # Seems that 'name' is a special attribute and this is (one of?) the
    # only way to do this.
    mocker.patch.object(
        exchange, 'name', new_callable=PropertyMock(return_value='Gemini'))
    return DryRunExecutor(exchange, mocker.Mock(), mocker.Mock())


@pytest.mark.parametrize("side", [BUY_SIDE, SELL_SIDE])
@pytest.mark.parametrize("order_type", [ORDER_TYPE_LIMIT, ORDER_TYPE_MARKET])
@pytest.mark.parametrize("symbol", ["ETH/USD", "ETH/KRW", "BTC/USD"])
@pytest.mark.parametrize("amount", [Decimal('10'), Decimal('25.5')])
@pytest.mark.parametrize("price", [Decimal('10'), Decimal('2000.55'), Decimal('1234567.89')])
@pytest.mark.parametrize("taker_fee", [Decimal('0.0015'), Decimal('0.0026')])
@pytest.mark.parametrize("buy_target_includes_fee", [True, False])
def test_complete_order(
        mocker, executor, side, order_type, symbol, amount, price, taker_fee,
        buy_target_includes_fee):
    mocker.patch.object(
        executor.fetcher, 'fetch_taker_fees', return_value=taker_fee)
    mocker.patch.object(
        executor.exchange, 'buy_target_includes_fee', buy_target_includes_fee)
    base, quote = split_symbol(symbol)

    result = executor._complete_order(side, order_type, symbol, amount, price)

    if side == BUY_SIDE:
        executor.dry_run_exchange.buy.assert_called_once()
    else:
        executor.dry_run_exchange.sell.assert_called_once()

    pre_fee_quote = amount * price

    if side == BUY_SIDE and buy_target_includes_fee:
        post_fee_base = amount * (ONE - taker_fee)
        post_fee_quote = pre_fee_quote
        fee_asset = base
        fees = amount - post_fee_base
    else:
        post_fee_base = amount
        fee_asset = quote
        if side == BUY_SIDE:
            post_fee_quote = pre_fee_quote * (ONE + taker_fee)
            fees = post_fee_quote - pre_fee_quote
        else:
            post_fee_quote = pre_fee_quote * (ONE - taker_fee)
            fees = pre_fee_quote - post_fee_quote

    assert result['pre_fee_base'] == amount
    assert result['pre_fee_quote'] == pre_fee_quote
    assert result['post_fee_base'] == post_fee_base
    assert result['post_fee_quote'] == post_fee_quote
    assert result['fees'] == fees
    assert result['fee_asset'] == fee_asset
    assert result['price'] == price
    assert result['true_price'] == post_fee_quote / post_fee_base
    assert result['side'] == side
    assert result['type'] == order_type


@pytest.mark.parametrize(
    "symbol, quote_amount, asset_price, slippage, test_id", [
        pytest.param('ETH/USD', 10000, 600, 1, 0),
        pytest.param('ETH/USD', 0, 600, 1, 1),
        pytest.param('ETH/USD', 10000, 2, 1, 2)
    ]
)
def test_create_emulated_market_buy_order(
        mocker, executor, exchange, symbol, quote_amount, asset_price,
        slippage, test_id):
    prepare = mocker.patch.object(exchange, 'prepare_emulated_market_buy_order')
    complete_order = mocker.patch.object(executor, '_complete_order')
    prepare.return_value = (round(quote_amount/asset_price, 6), None)

    executor.create_emulated_market_buy_order(
        symbol, quote_amount, asset_price, slippage)

    complete_order.assert_called_once_with(
        BUY_SIDE, ORDER_TYPE_LIMIT, symbol, prepare.return_value[0],
        asset_price)


@pytest.mark.parametrize(
    "symbol, asset_price, asset_amount, slippage, test_id", [
        pytest.param('ETH/USD', 600, 2, 1, 0),
        pytest.param('ETH/USD', 0, 2, 1, 1),
        pytest.param('ETH/USD', 600, 0, 1, 2),
        pytest.param('ETH/USD', 0, 0, 1, 3)
    ]
)
def test_create_emulated_market_sell_order(
        mocker, executor, exchange, symbol, asset_price, asset_amount,
        slippage, test_id):
    prepare = mocker.patch.object(exchange, 'prepare_emulated_market_sell_order')
    complete_order = mocker.patch.object(executor, '_complete_order')
    prepare.return_value = (round(asset_amount, 6), None)

    executor.create_emulated_market_sell_order(
        symbol, asset_price, asset_amount, slippage)

    complete_order.assert_called_once_with(
        SELL_SIDE, ORDER_TYPE_LIMIT, symbol, prepare.return_value[0],
        asset_price)


@pytest.mark.parametrize(
    "symbol, asset_amount, asset_price, test_id", [
        ('ETH/USD', 2, 600, 0),
        (None, None, None, 1)
    ]
)
def test_create_market_buy_order(
        mocker, executor, symbol, asset_amount, asset_price, test_id):
    complete_order = mocker.patch.object(executor, '_complete_order')

    executor.create_market_buy_order(symbol, asset_amount, asset_price)

    complete_order.assert_called_once_with(
        BUY_SIDE, ORDER_TYPE_MARKET, symbol, asset_amount, asset_price)

@pytest.mark.parametrize(
    "symbol, asset_amount, asset_price, test_id", [
        ('ETH/USD', 2, 600, 0),
        (None, None, None, 1)
    ]
)
def test_create_market_sell_order(
        mocker, executor, symbol, asset_amount, asset_price, test_id):
    complete_order = mocker.patch.object(executor, '_complete_order')

    executor.create_market_sell_order(symbol, asset_amount, asset_price)

    complete_order.assert_called_once_with(
        SELL_SIDE, ORDER_TYPE_MARKET, symbol, asset_amount, asset_price)
