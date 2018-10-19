from decimal import Decimal, DefaultContext, setcontext

import pytest

import autotrageur.bot.arbitrage.spreadcalculator as spreadcalculator
from fp_libs.utilities import set_autotrageur_decimal_context


@pytest.fixture(scope="module", autouse=True)
def set_default_context():
    setcontext(DefaultContext)
    yield
    set_autotrageur_decimal_context()

# Test parameters.
price_params_return_none = [
    (None, None),
    (None, Decimal('100.00')),
    (Decimal('0'), Decimal('0')),
    (Decimal('0'), Decimal('100')),
    (Decimal('100'), Decimal('0')),
    (Decimal('100.00'), None)
]

fee_params_return_none = [
    (Decimal('0.10'), Decimal('0.01')),
    (Decimal('0'), Decimal('0')),
    (None, None),
    (0, 0),
    (99999.999999, Decimal('99999.999999'))
]

price_fees_exceptions_params = [
    (Decimal('100.00'), Decimal('100.00'), 0.01, 0.01),
    (Decimal('100.00'), Decimal('100.00'), Decimal('0.01'), 0.01),
    (Decimal('100.00'), Decimal('100.00'), 0.01, Decimal('0.01')),
    (Decimal('100.00'), 100.00, Decimal('0.10'), Decimal('0.10')),
    (100.00, Decimal('100.00'), Decimal('0.10'), Decimal('0.10')),
    (Decimal('100.00'), 100.00, Decimal('0.10'), 0.01),
    (Decimal('100.00'), 100.00, 0.01, 0.01),
    (Decimal('100.00'), Decimal('100.00'), Decimal('0.10'), 0.01),
    (Decimal('100.00'), Decimal('100.00'),  0.01, Decimal('0.10')),
]

@pytest.mark.parametrize('buy_price, sell_price', price_params_return_none)
def test_is_invalid_price_true(buy_price, sell_price):
    result = spreadcalculator._is_invalid_price(buy_price, sell_price)
    assert result is True

@pytest.mark.parametrize('buy_price, sell_price', [
    (Decimal('0.000001'), Decimal('0.000001')),
    (Decimal('0.000001'), Decimal('100.00')),
    (Decimal('0.000001'), Decimal('999999')),
    (Decimal('999999'), Decimal('100')),
    (Decimal('100'), Decimal('999999')),
    (Decimal('100.00'), Decimal('0.000001'))
])
def test_is_invalid_price_false(buy_price, sell_price):
    result = spreadcalculator._is_invalid_price(buy_price, sell_price)
    assert result is False

class TestCalcSpread:
    @pytest.mark.parametrize('buy_price, sell_price, buy_fee, sell_fee, spread', [
        # Same prices, no fees.
        (Decimal('100'), Decimal('100'), Decimal('0.0'), Decimal('0.0'), Decimal('0')),
        # No fees, large profit from small buy_price, large sell_price.
        (Decimal('100.00'), Decimal('1000000.00'), Decimal('0.0'), Decimal('0.0'), Decimal('999900.000000')),
        # No fees, negative large profit from large buy_price, small sell_price.
        (Decimal('1000000.00'), Decimal('100.00'), Decimal('0.0'), Decimal('0.0'), Decimal('-99.9900000000')),
        # Same prices, 10% buy fee.
        (Decimal('100'), Decimal('100'), Decimal('0.1'), Decimal('0.0'), Decimal('-10.0000')),
        # Same prices, 10% sell fee.
        (Decimal('100'), Decimal('100'), Decimal('0.0'), Decimal('0.1'), Decimal('-10.0000')),
        # Double of the numerator 50% buy fees, 0% sell fees cancel out to 0.
        (Decimal('1'), Decimal('2'), Decimal('0.5'), Decimal('0.0'), Decimal('0')),
        # Inverse of the above
        (Decimal('2'), Decimal('1'), Decimal('0.0'), Decimal('0.5'), Decimal('-75.00')),
        # More realistic scenario with 1% fees.
        (Decimal('1.00'), Decimal('1.05'), Decimal('0.01'), Decimal('0.01'), Decimal('2.910500')),
        # Inverse of the above.
        (Decimal('1.05'), Decimal('1.00'), Decimal('0.01'), Decimal('0.01'), Decimal('-6.657142857142857142857142850')),
        # Forward spread opportunity, +5%, no fees.
        (Decimal('1.00'), Decimal('1.05'), Decimal('0'), Decimal('0'), Decimal('5')),
        # Reverse spread opportunity, inverse of above, no fees.
        (Decimal('1.05'), Decimal('1.00'), Decimal('0'), Decimal('0'), Decimal('-4.761904761904761904761904760')),
        # Forward spread opportunity, around +3%, with fees, longer precision.
        (Decimal('100000.12345678'), Decimal('105000.12963069'), Decimal('0.0095238'), Decimal('0.01'), Decimal('2.960000991050190713566361200')),
        # Inverse of above. Reverse spread opportunity, around -3%, with fees, longer precision.
        (Decimal('105000.12963069'), Decimal('100000.12345678'), Decimal('0.01'), Decimal('0.0095238'), Decimal('-6.612244000952553935197867780')),
    ])
    def test_calc_fixed_spread_buy_fee_incl(self, mocker, buy_price, sell_price, buy_fee, sell_fee, spread):
        mocker.spy(spreadcalculator, '_is_invalid_price')
        result_spread = spreadcalculator.calc_fixed_spread(buy_price, sell_price, buy_fee, sell_fee, True)
        spreadcalculator._is_invalid_price.assert_called_once_with(buy_price, sell_price)
        assert result_spread == spread

    @pytest.mark.parametrize('buy_price, sell_price, buy_fee, sell_fee, spread', [
        # Same prices, no fees.
        (Decimal('100'), Decimal('100'), Decimal('0.0'), Decimal('0.0'), Decimal('0')),
        # No fees, large profit from small buy_price, large sell_price.
        (Decimal('100.00'), Decimal('1000000.00'), Decimal('0.0'), Decimal('0.0'), Decimal('999900.000000')),
        # No fees, negative large profit from large buy_price, small sell_price.
        (Decimal('1000000.00'), Decimal('100.00'), Decimal('0.0'), Decimal('0.0'), Decimal('-99.9900000000')),
        # Same prices, 10% buy fee.
        (Decimal('100'), Decimal('100'), Decimal('0.1'), Decimal('0.0'), Decimal('-9.090909090909090909090909090')),
        # Same prices, 10% sell fee.
        (Decimal('100'), Decimal('100'), Decimal('0.0'), Decimal('0.1'), Decimal('-10.000')),
        # Double of the numerator 50% buy fees, 0% sell fees.
        (Decimal('1'), Decimal('2'), Decimal('0.5'), Decimal('0.0'), Decimal('33.33333333333333333333333330')),
        # Inverse of the above
        (Decimal('2'), Decimal('1'), Decimal('0.0'), Decimal('0.5'), Decimal('-75.00')),
        # More realistic scenario with 1% fees.
        (Decimal('1.00'), Decimal('1.05'), Decimal('0.01'), Decimal('0.01'), Decimal('2.920792079207920792079208000')),
        # Inverse of the above.
        (Decimal('1.05'), Decimal('1.00'), Decimal('0.01'), Decimal('0.01'), Decimal('-6.647807637906647807637906640')),
        # Forward spread opportunity, +5%, no fees.
        (Decimal('1.00'), Decimal('1.05'), Decimal('0'), Decimal('0'), Decimal('5')),
        # Reverse spread opportunity, inverse of above, no fees.
        (Decimal('1.05'), Decimal('1.00'), Decimal('0'), Decimal('0'), Decimal('-4.761904761904761904761904760')),
        # Forward spread opportunity, around +3%, with fees, longer precision.
        (Decimal('100000.12345678'), Decimal('105000.12963069'), Decimal('0.0095238'), Decimal('0.01'), Decimal('2.969340595100668940149527300')),
        # Inverse of above. Reverse spread opportunity, around -3%, with fees, longer precision.
        (Decimal('105000.12963069'), Decimal('100000.12345678'), Decimal('0.01'), Decimal('0.0095238'), Decimal('-6.602904291381692104408308630')),
    ])
    def test_calc_fixed_spread_buy_fee_not_incl(self, mocker, buy_price, sell_price, buy_fee, sell_fee, spread):
        mocker.spy(spreadcalculator, '_is_invalid_price')
        result_spread = spreadcalculator.calc_fixed_spread(buy_price, sell_price, buy_fee, sell_fee, False)
        spreadcalculator._is_invalid_price.assert_called_once_with(buy_price, sell_price)
        assert result_spread == spread

    @pytest.mark.parametrize('buy_price, sell_price', price_params_return_none)
    @pytest.mark.parametrize('buy_fee, sell_fee', fee_params_return_none)
    def test_calc_fixed_spread_return_none(self, buy_price, sell_price, buy_fee, sell_fee):
        result_spread = spreadcalculator.calc_fixed_spread(buy_price, sell_price, buy_fee, sell_fee, False)
        assert result_spread is None

    @pytest.mark.parametrize('buy_price, sell_price, buy_fee, sell_fee', price_fees_exceptions_params)
    def test_calc_fixed_spread_exceptions(self, buy_price, sell_price, buy_fee, sell_fee):
        with pytest.raises(TypeError, message='mixed float and decimal arithmetic'):
            spreadcalculator.calc_fixed_spread(buy_price, sell_price, buy_fee, sell_fee, False)
