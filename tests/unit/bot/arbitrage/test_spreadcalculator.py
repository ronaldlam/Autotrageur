from decimal import Decimal

import pytest

import bot.arbitrage.spreadcalculator as spreadcalculator


class TestCalcSpread:
    @pytest.mark.parametrize('exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee, spread', [
        # Double of the numerator 50% fees cancel out to 0.
        (Decimal('2'), Decimal('1'), Decimal('0.5'), Decimal('0.0'), Decimal('0')),
        # More realistic scenario with fees canceling percentage.
        (Decimal('1.05'), Decimal('1.00'), Decimal('0.025'), Decimal('0.02375'), Decimal('0')),
        # Inverse of the above.
        (Decimal('1.00'), Decimal('1.05'), Decimal('0.02375'), Decimal('0.025'), Decimal('0')),
        # Forward spread opportunity, +5%, no fees.
        (Decimal('1.05'), Decimal('1.00'), Decimal('0'), Decimal('0'), Decimal('5')),
        # Reverse spread opportunity, -5%, no fees.
        (Decimal('1.00'), Decimal('1.05'), Decimal('0'), Decimal('0'), Decimal('-5')),
        # Forward spread opportunity, around +3%, with fees, longer precision.
        (Decimal('105000.12963069'), Decimal('100000.12345678'), Decimal('0.0095238'), Decimal('0.01'), Decimal('3.000001001060798700572081992')),
        # Inverse of above. Reverse spread opportunity, around -3%, with fees, longer precision.
        (Decimal('100000.12345678'), Decimal('105000.12963069'), Decimal('0.01'), Decimal('0.0095238'), Decimal('-3.000001001060798700572081992')),
    ])
    def test_calc_spread(self, mocker, exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee, spread):
        mocker.spy(spreadcalculator, 'calc_trade_fees')
        result_spread = spreadcalculator.calc_spread(exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee)

        if exc2_num_price >= exc1_denom_price:
            spreadcalculator.calc_trade_fees.assert_called_with(exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee) # pylint: disable=no-member
        else:
            spreadcalculator.calc_trade_fees.assert_called_with(exc1_denom_price, exc2_num_price, exc1_fee, exc2_fee) # pylint: disable=no-member
        assert result_spread == spread

    @pytest.mark.parametrize('exc2_num_price, exc1_denom_price', [
        (None, None),
        (None, Decimal('100.00')),
        (Decimal('0'), Decimal('0')),
        (Decimal('100.00'), None)
    ])
    @pytest.mark.parametrize('exc2_fee, exc1_fee', [
        (Decimal('0.10'), Decimal('0.01')),
        (Decimal('0'), Decimal('0')),
        (None, None),
        (0, 0),
        (99999.999999, Decimal('99999.999999'))
    ])
    def test_calc_spread_return_none(self, exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee):
        result_spread = spreadcalculator.calc_spread(exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee)
        assert result_spread is None

    @pytest.mark.parametrize('exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee', [
        (Decimal('100.00'), Decimal('100.00'), 0.01, 0.01),
        (Decimal('100.00'), Decimal('100.00'), Decimal('0.01'), 0.01),
        (Decimal('100.00'), Decimal('100.00'), 0.01, Decimal('0.01')),
        (Decimal('100.00'), 100.00, Decimal('0.10'), Decimal('0.10')),
        (100.00, Decimal('100.00'), Decimal('0.10'), Decimal('0.10')),
        (Decimal('100.00'), 100.00, Decimal('0.10'), 0.01),
        (Decimal('100.00'), 100.00, 0.01, 0.01),
        (Decimal('100.00'), Decimal('100.00'), Decimal('0.10'), 0.01),
        (Decimal('100.00'), Decimal('100.00'),  0.01, Decimal('0.10')),
    ])
    def test_calc_spread_exceptions(self, exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee):
        with pytest.raises(TypeError, reason='mixed float and decimal arithmetic'):
            spreadcalculator.calc_spread(exc2_num_price, exc1_denom_price, exc2_fee, exc1_fee)


class TestCalcTradeFees:
    @pytest.mark.parametrize('price1, price2, fee1, fee2, trade_fees', [
        (Decimal('0'), Decimal('0'), Decimal('0.01'), Decimal('0.03'), Decimal('0')),
        (Decimal('100'), Decimal('0'), Decimal('0.01'), Decimal('0.03'), Decimal('0.01')),
        (Decimal('0'), Decimal('100'), Decimal('0.01'), Decimal('0.03'), Decimal('0.03')),
        (Decimal('1.05'), Decimal('1.00'), Decimal('0'), Decimal('0'), Decimal('0')),
        (Decimal('1.00'), Decimal('1.05'), Decimal('0'), Decimal('0'), Decimal('0')),
        (Decimal('1.00'), Decimal('1.00'), Decimal('0.025'), Decimal('0.025'), Decimal('5')),
        (Decimal('1.05'), Decimal('1.00'), Decimal('0.025'), Decimal('0.025'), Decimal('5.125')),
        (Decimal('1.00'), Decimal('1.05'), Decimal('0.025'), Decimal('0.025'), Decimal('5.125')),
        (Decimal('105000.12963069'), Decimal('100000.12345678'), Decimal('0.0095238'), Decimal('0.01'), Decimal('1.999999000010199977207436579')),
        (Decimal('100000.12345678'), Decimal('105000.12963069'), Decimal('0.01'), Decimal('0.0095238'), Decimal('1.999999000010199977207436579')),
    ])
    def test_calc_trade_fees(self, price1, price2, fee1, fee2, trade_fees):
        result_fees = spreadcalculator.calc_trade_fees(price1, price2, fee1, fee2)
        assert result_fees == trade_fees
