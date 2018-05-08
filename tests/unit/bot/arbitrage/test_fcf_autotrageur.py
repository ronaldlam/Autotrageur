import decimal
import pytest

import bot.arbitrage.fcf_autotrageur
from bot.arbitrage.fcf_autotrageur import FCFAutotrageur
import libs.email_client.simple_email_client


xfail = pytest.mark.xfail


@pytest.fixture()
def fcf_autotrageur():
    f = FCFAutotrageur()
    f.config = {
        'email_cfg_path': 'fake/path/to/config.yaml'
    }
    f.message = 'fake message'
    return f

class TestIsWithinTolerance:
    @pytest.mark.parametrize('curr_spread, prev_spread, spread_rnd, spread_tol, bTol', [
        (0, 0, 0, 0, True),
        (0, 0, None, 0, True),
        (0, 0, 0, 1, True),
        (0, 0, None, 1, True),
        (0.0, 1.0, 1, 1.0, True),
        (0.0, 1.0, None, 1.0, True),
        (1.0, 0.0, 1, 1.0, True),
        (1.0, 0.0, None, 1.0, True),
        (0.0, 1.1, 1, 1.0, False),
        (0.0, 1.1, None, 1.0, False),
        (100.001, 100.002, None, 0.001, True),
        (100.001, 100.002, 0, 0.001, True),
        (100.001, 100.002, 100, 0.001, True),
        (100.001, 100.002, None, 0.0001, False),
        (1000000.12345678, 1000000.12345679, None, 0.00000001, True),
        (1000000.12345678, 1000000.12345679, 1, 0.00000001, True),
        (1000000.12345678, 1000000.12345679, None, 0.000000001, False)
    ])
    def test_is_within_tolerance(self, fcf_autotrageur, curr_spread, prev_spread,
                                spread_rnd, spread_tol, bTol):
        bWithinTol = FCFAutotrageur._is_within_tolerance(curr_spread, prev_spread,
                                                        spread_rnd, spread_tol)
        assert bWithinTol is bTol

    @pytest.mark.parametrize('curr_spread, prev_spread, spread_rnd, spread_tol, bTol', [
        (None, None, None, None, True),
        (None, 1, 1, 0.1, True),
        (1, None, 1, 0.1, True),
        (1, 1, 1, None, True)
    ])
    def test_is_within_tolerance_bad(self, fcf_autotrageur, curr_spread, prev_spread,
                                spread_rnd, spread_tol, bTol):
        with pytest.raises((decimal.InvalidOperation, TypeError), message="Expecting a float, not a NoneType"):
            bWithinTol = FCFAutotrageur._is_within_tolerance(curr_spread, prev_spread,
                                                                spread_rnd, spread_tol)
            assert bWithinTol is bTol


class TestEmailOrThrottle:
    @pytest.mark.parametrize('email_count, prev_spread, curr_spread, max_emails, rnding, tol', [
        (0, 0.0, 2.0, 2, 1, 0.1),
        (1, 2.0, 2.0, 2, 1, 0.1),
        (2, 2.0, 5.0, 2, 1, 0.1)
    ])
    def test_email_or_throttle_emailed(self, mocker, fcf_autotrageur, email_count,
                                    prev_spread, curr_spread, max_emails,
                                    rnding, tol):
        mock_send_all_emails = mocker.patch('bot.arbitrage.fcf_autotrageur.send_all_emails', autospec=True)
        mocker.patch.object(bot.arbitrage.fcf_autotrageur, 'email_count', email_count)
        mocker.patch.object(bot.arbitrage.fcf_autotrageur, 'prev_spread', prev_spread)

        fcf_autotrageur.config['max_emails'] = max_emails
        fcf_autotrageur.config['spread_rounding'] = rnding
        fcf_autotrageur.config['spread_tolerance'] = tol

        fcf_autotrageur._email_or_throttle(curr_spread)
        assert mock_send_all_emails.called


    @pytest.mark.parametrize('email_count, prev_spread, curr_spread, max_emails, rnding, tol', [
        (0, 0, 0, 0, 0, 0),
        pytest.param(0, 0, None, 0, 0, 0, marks=xfail(raises=(TypeError, decimal.InvalidOperation), reason="rounding or arithmetic on NoneType", strict=True)),
        (2, 2.0, 2.0, 2, 1, 0.1),
        (2, 2.0, 2.1, 2, 1, 0.1),
        (2, 2.1, 2.0, 2, 1, 0.1)
    ])
    def test_email_or_throttle_throttled(self, mocker, fcf_autotrageur, email_count,
                                    prev_spread, curr_spread, max_emails,
                                    rnding, tol):
        mock_send_all_emails = mocker.patch('bot.arbitrage.fcf_autotrageur.send_all_emails', autospec=True)
        mocker.patch.object(bot.arbitrage.fcf_autotrageur, 'email_count', email_count)
        mocker.patch.object(bot.arbitrage.fcf_autotrageur, 'prev_spread', prev_spread)

        fcf_autotrageur.config['max_emails'] = max_emails
        fcf_autotrageur.config['spread_rounding'] = rnding
        fcf_autotrageur.config['spread_tolerance'] = tol

        fcf_autotrageur._email_or_throttle(curr_spread)
        assert not mock_send_all_emails.called