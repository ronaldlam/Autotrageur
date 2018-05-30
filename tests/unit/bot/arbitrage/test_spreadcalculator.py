from decimal import Decimal, DefaultContext, setcontext

import pytest

import bot.arbitrage.spreadcalculator as spreadcalculator
from libs.utilities import set_autotrageur_decimal_context


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

@pytest.mark.parametrize('price1, price2', price_params_return_none)
def test_is_invalid_price_true(price1, price2):
    result = spreadcalculator.__is_invalid_price(price1, price2)
    assert result is True

@pytest.mark.parametrize('price1, price2', [
    (Decimal('0.000001'), Decimal('0.000001')),
    (Decimal('0.000001'), Decimal('100.00')),
    (Decimal('0.000001'), Decimal('999999')),
    (Decimal('999999'), Decimal('100')),
    (Decimal('100'), Decimal('999999')),
    (Decimal('100.00'), Decimal('0.000001'))
])
def test_is_invalid_price_false(price1, price2):
    result = spreadcalculator.__is_invalid_price(price1, price2)
    assert result is False

class TestCalcSpread:
    @pytest.mark.parametrize('exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee, spread', [
        # Double of the numerator 50% fees cancel out to 0.
        (Decimal('1'), Decimal('2'), Decimal('0.5'), Decimal('0.0'), Decimal('0')),
        # More realistic scenario with 1% fees.
        (Decimal('1.00'), Decimal('1.05'), Decimal('0.01'), Decimal('0.01'), Decimal('2.910500')),
        # Inverse of the above.
        (Decimal('1.05'), Decimal('1.00'), Decimal('0.01'), Decimal('0.01'), Decimal('-6.657142857142857142857142850')),
        # Forward spread opportunity, +5%, no fees.
        (Decimal('1.00'), Decimal('1.05'), Decimal('0'), Decimal('0'), Decimal('5')),
        # Reverse spread opportunity, -5%, no fees.
        (Decimal('1.05'), Decimal('1.00'), Decimal('0'), Decimal('0'), Decimal('-4.761904761904761904761904760')),
        # Forward spread opportunity, around +3%, with fees, longer precision.
        (Decimal('100000.12345678'), Decimal('105000.12963069'), Decimal('0.0095238'), Decimal('0.01'), Decimal('2.960000991050190713566361200')),
        # Inverse of above. Reverse spread opportunity, around -3%, with fees, longer precision.
        (Decimal('105000.12963069'), Decimal('100000.12345678'), Decimal('0.01'), Decimal('0.0095238'), Decimal('-6.612244000952553935197867780')),
    ])
    def test_calc_fixed_spread(self, mocker, exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee, spread):
        result_spread = spreadcalculator.calc_fixed_spread(exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee)

        # spreadcalculator.calc_trade_fees.assert_called_with(exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee) # pylint: disable=no-member
        assert result_spread == spread

    @pytest.mark.parametrize('exc2_num_price, exc1_denom_price', price_params_return_none)
    @pytest.mark.parametrize('exc2_fee, exc1_fee', fee_params_return_none)
    def test_calc_fixed_spread_return_none(self, exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee):
        result_spread = spreadcalculator.calc_fixed_spread(exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee)
        assert result_spread is None

    @pytest.mark.parametrize('exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee', price_fees_exceptions_params)
    def test_calc_fixed_spread_exceptions(self, exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee):
        with pytest.raises(TypeError, reason='mixed float and decimal arithmetic'):
            spreadcalculator.calc_fixed_spread(exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee)
