from decimal import Decimal

import pytest

from autotrageur.bot.trader.dry_run import DryRunExchange, InsufficientFakeFunds


START_BALANCE = Decimal('100')


@pytest.fixture()
def exchange():
    return DryRunExchange('gemini', 'ETH', 'USD', 100, 100)


class TestDryRunExchange:

    @pytest.mark.parametrize("name", ['gemini', 'bithumb'])
    @pytest.mark.parametrize("base", ['ETH', 'BTC'])
    @pytest.mark.parametrize("quote", ['USD', 'KRW'])
    @pytest.mark.parametrize("base_balance", ['123', 123.456, 123])
    @pytest.mark.parametrize("quote_balance", ['123', 123.456, 123])
    def test_init(self, name, base, quote, base_balance, quote_balance):
        exchange = DryRunExchange(
            name, base, quote, base_balance, quote_balance)

        assert exchange.name == name
        assert exchange.base == base
        assert exchange.quote == quote
        assert exchange.trade_count == 0
        assert isinstance(exchange.base_balance, Decimal)
        assert isinstance(exchange.quote_balance, Decimal)
        assert isinstance(exchange.base_volume, Decimal)
        assert isinstance(exchange.quote_volume, Decimal)
        assert isinstance(exchange.base_fees, Decimal)
        assert isinstance(exchange.quote_fees, Decimal)

    @pytest.mark.parametrize(
        'pre_fee_base, pre_fee_quote, post_fee_base, post_fee_quote', [
            (Decimal('10'), Decimal('99'), Decimal('10'), Decimal('100')),
            (Decimal('10'), Decimal('100'), Decimal('9.9'), Decimal('100')),
        ])
    def test_buy(self, exchange, pre_fee_base, pre_fee_quote, post_fee_base,
                 post_fee_quote):
        exchange.buy(
            pre_fee_base, pre_fee_quote, post_fee_base, post_fee_quote)

        assert exchange.base_balance == START_BALANCE + post_fee_base
        assert exchange.quote_balance == START_BALANCE - post_fee_quote
        assert exchange.base_volume == pre_fee_base
        assert exchange.quote_volume == pre_fee_quote
        assert exchange.base_fees == pre_fee_base - post_fee_base
        assert exchange.quote_fees == post_fee_quote - pre_fee_quote
        assert exchange.trade_count == 1

    @pytest.mark.parametrize(
        'pre_fee_base, pre_fee_quote, post_fee_base, post_fee_quote', [
            (Decimal('10'), Decimal('99'), Decimal('10'), Decimal('101')),
            (Decimal('10'), Decimal('101'), Decimal('10'), Decimal('102')),
            (Decimal('10'), Decimal('200'), Decimal('9.9'), Decimal('200')),
        ])
    def test_bad_buy(self, exchange, pre_fee_base, pre_fee_quote, post_fee_base,
                 post_fee_quote):
        with pytest.raises(InsufficientFakeFunds):
            exchange.buy(
                pre_fee_base, pre_fee_quote, post_fee_base, post_fee_quote)

    @pytest.mark.parametrize(
        'base_amount, pre_fee_quote, post_fee_quote', [
            (Decimal('10'), Decimal('100'), Decimal('99')),
            (Decimal('20'), Decimal('100'), Decimal('99.9')),
        ])
    def test_sell(self, exchange, base_amount, pre_fee_quote, post_fee_quote):
        exchange.sell(base_amount, pre_fee_quote, post_fee_quote)

        assert exchange.base_balance == START_BALANCE - base_amount
        assert exchange.quote_balance == START_BALANCE + post_fee_quote
        assert exchange.base_volume == base_amount
        assert exchange.quote_volume == pre_fee_quote
        assert exchange.base_fees == Decimal('0')
        assert exchange.quote_fees == pre_fee_quote - post_fee_quote
        assert exchange.trade_count == 1

    @pytest.mark.parametrize(
        'base_amount, pre_fee_quote, post_fee_quote', [
            (Decimal('101'), Decimal('100'), Decimal('99')),
            (Decimal('200'), Decimal('100'), Decimal('99.9')),
            (Decimal('100.000001'), Decimal('100'), Decimal('99')),
        ])
    def test_bad_sell(self, exchange, base_amount, pre_fee_quote, post_fee_quote):
        with pytest.raises(InsufficientFakeFunds):
            exchange.sell(base_amount, pre_fee_quote, post_fee_quote)
