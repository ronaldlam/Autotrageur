from decimal import Decimal, InvalidOperation

from ccxt import NetworkError
import pytest

import bot.arbitrage.fcf_autotrageur
from bot.arbitrage.fcf_autotrageur import (
    FCFAutotrageur, arbseeker, email_count, prev_spread, EMAIL_HIGH_SPREAD_HEADER,
    EMAIL_LOW_SPREAD_HEADER, EMAIL_NONE_SPREAD)
import libs.email_client.simple_email_client


xfail = pytest.mark.xfail


@pytest.fixture()
def fcf_autotrageur(mocker, fake_ccxt_trader):
    f = FCFAutotrageur()
    f.config = {
        'email_cfg_path': 'fake/path/to/config.yaml',
        'spread_target_low': 1.0,
        'spread_target_high': 5.0
    }
    mocker.patch.object(f, 'tclient1', fake_ccxt_trader, create=True)
    mocker.patch.object(f, 'tclient2', fake_ccxt_trader, create=True)
    f.message = 'fake message'
    # f.spread_opp = { arbseeker.SPREAD: 1.0 }
    return f

class TestIsWithinTolerance:
    @pytest.mark.parametrize('curr_spread, prev_spread, spread_rnd, spread_tol, bTol', [
        (Decimal('0'), Decimal('0'), 0, Decimal('0'), True),
        (Decimal('0'), Decimal('0'), None, Decimal('0'), True),
        (Decimal('0'), Decimal('0'), 0, Decimal('1'), True),
        (Decimal('0'), Decimal('0'), None, Decimal('1'), True),
        (Decimal('0.0'), Decimal('1.0'), 1, Decimal('1.0'), True),
        (Decimal('0.0'), Decimal('1.0'), None, Decimal('1.0'), True),
        (Decimal('1.0'), Decimal('0.0'), 1, Decimal('1.0'), True),
        (Decimal('1.0'), Decimal('0.0'), None, Decimal('1.0'), True),
        (Decimal('0.0'), Decimal('1.1'), 1, Decimal('1.0'), False),
        (Decimal('0.0'), Decimal('1.1'), None, Decimal('1.0'), False),
        (Decimal('100.001'), Decimal('100.002'), None, Decimal('0.001'), True),
        (Decimal('100.001'), Decimal('100.002'), 0, Decimal('0.001'), True),
        (Decimal('100.001'), Decimal('100.002'), 20, Decimal('0.001'), True),
        (Decimal('100.001'), Decimal('100.002'), None, Decimal('0.0001'), False),
        (Decimal('1000000.12345678'), Decimal('1000000.12345679'), None, Decimal('0.00000001'), True),
        (Decimal('1000000.12345678'), Decimal('1000000.12345679'), 1, Decimal('0.00000001'), True),
        (Decimal('1000000.12345678'), Decimal('1000000.12345679'), None, Decimal('0.000000001'), False)
    ])
    def test_is_within_tolerance(
        self, curr_spread, prev_spread, spread_rnd, spread_tol, bTol):
        in_tolerance = FCFAutotrageur._is_within_tolerance(
            curr_spread, prev_spread, spread_rnd, spread_tol)
        assert in_tolerance is bTol

    @pytest.mark.parametrize('curr_spread, prev_spread, spread_rnd, spread_tol, bTol', [
        (None, None, None, None, True),
        (None, Decimal('1'), 1, Decimal('0.1'), True),
        (Decimal('1'), None, 1, Decimal('0.1'), True),
        (Decimal('1'), Decimal('1'), 1, None, True)
    ])
    def test_is_within_tolerance_bad(
        self, curr_spread, prev_spread, spread_rnd, spread_tol, bTol):
        with pytest.raises((InvalidOperation, TypeError), message="Expecting a Decimal or int, not a NoneType"):
            in_tolerance = FCFAutotrageur._is_within_tolerance(
                curr_spread, prev_spread, spread_rnd, spread_tol)
            assert in_tolerance is bTol


# class TestPollOpportunity:
#     @pytest.mark.parametrize('is_network_err', [ True, False ])
#     @pytest.mark.parametrize('spread_opp', [
#         None,
#         { arbseeker.SPREAD_OPP_TYPE: SpreadOpportunity.HIGH },
#         { arbseeker.SPREAD_OPP_TYPE: SpreadOpportunity.LOW },
#     ])
#     def test_poll_opportunity(self, mocker, fcf_autotrageur, spread_opp, is_network_err):
#         mocker.patch.object(fcf_autotrageur, '_FCFAutotrageur__set_message')

#         mock_get_arb_opps = mocker.patch.object(arbseeker,
#                 'get_arb_opportunities_by_orderbook', return_value=spread_opp)

#         if is_network_err:
#             mock_get_arb_opps.side_effect = NetworkError
#             fcf_autotrageur.spread_opp = None

#         is_opportunity = fcf_autotrageur._poll_opportunity()

#         if fcf_autotrageur.spread_opp is None:
#             assert not is_opportunity
#             fcf_autotrageur._FCFAutotrageur__set_message.assert_called_with(None)
#         elif fcf_autotrageur.spread_opp[arbseeker.SPREAD_OPP_TYPE] is SpreadOpportunity.HIGH:
#             assert is_opportunity
#             fcf_autotrageur._FCFAutotrageur__set_message.assert_called_with(SpreadOpportunity.HIGH)
#         elif fcf_autotrageur.spread_opp[arbseeker.SPREAD_OPP_TYPE] is SpreadOpportunity.LOW:
#             assert is_opportunity
#             fcf_autotrageur._FCFAutotrageur__set_message.assert_called_with(SpreadOpportunity.LOW)
#         else:
#             pytest.fail("Shouldn't reach here.")


class TestEmailOrThrottle:
    def _setup_pre_email(self, mocker, fcf_autotrageur, fake_email_count,
                         fake_prev_spread, max_emails, rnding, tol):
        mock_send_all_emails = mocker.patch('bot.arbitrage.fcf_autotrageur.send_all_emails', autospec=True)
        mocker.patch('bot.arbitrage.fcf_autotrageur.email_count', fake_email_count)
        mocker.patch('bot.arbitrage.fcf_autotrageur.prev_spread', fake_prev_spread)

        fcf_autotrageur.config['max_emails'] = max_emails
        fcf_autotrageur.config['spread_rounding'] = rnding
        fcf_autotrageur.config['spread_tolerance'] = tol

        # Check before actual call made.
        assert bot.arbitrage.fcf_autotrageur.email_count == fake_email_count
        assert bot.arbitrage.fcf_autotrageur.prev_spread == fake_prev_spread

        return mock_send_all_emails

    @pytest.mark.parametrize('fake_email_count, next_email_count, fake_prev_spread, curr_spread, max_emails, rnding, tol', [
        (0, 1, Decimal('0.0'), Decimal('2.0'), 2, 1, 0.1),
        (1, 2, Decimal('2.0'), Decimal('2.0'), 2, 1, 0.1),
        (2, 1, Decimal('2.0'), Decimal('5.0'), 2, 1, 0.1)
    ])
    def test_FCFAutotrageur__email_or_throttle_emailed(self, mocker, fcf_autotrageur, fake_email_count,
                                       next_email_count, fake_prev_spread, curr_spread, max_emails,
                                       rnding, tol):
        mock_send_all_emails = self._setup_pre_email(mocker, fcf_autotrageur, fake_email_count,
            fake_prev_spread, max_emails, rnding, tol)

        fcf_autotrageur._FCFAutotrageur__email_or_throttle(curr_spread)
        assert mock_send_all_emails.called

        # Check email_count after actual call; should be incremented by 1.
        assert bot.arbitrage.fcf_autotrageur.email_count == next_email_count

    @pytest.mark.parametrize('fake_email_count, next_email_count, fake_prev_spread, curr_spread, max_emails, rnding, tol', [
        (0, 0, Decimal('0'), Decimal('0'), 0, 0, 0),
        pytest.param(0, 0, Decimal('0'), None, 0, 0, 0, marks=xfail(raises=(TypeError, InvalidOperation), reason="rounding or arithmetic on NoneType", strict=True)),
        (2, 2, Decimal('2.0'), Decimal('2.0'), 2, 1, 0.1),
        (2, 2, Decimal('2.0'), Decimal('2.1'), 2, 1, 0.1),
        (2, 2, Decimal('2.1'), Decimal('2.0'), 2, 1, 0.1)
    ])
    def test_FCFAutotrageur__email_or_throttle_throttled(self, mocker, fcf_autotrageur, fake_email_count,
                                         next_email_count, fake_prev_spread, curr_spread, max_emails,
                                         rnding, tol):
        mock_send_all_emails = self._setup_pre_email(mocker, fcf_autotrageur, fake_email_count,
            fake_prev_spread, max_emails, rnding, tol)

        fcf_autotrageur._FCFAutotrageur__email_or_throttle(curr_spread)
        assert not mock_send_all_emails.called

        # Check email_count after actual call; should not be incremented by 1.
        assert bot.arbitrage.fcf_autotrageur.email_count == next_email_count

# @pytest.mark.parametrize('opp_type', [
#     None,
#     SpreadOpportunity.LOW,
#     SpreadOpportunity.HIGH
# ])
# def test_FCFAutotrageur__set_message(mocker, fcf_autotrageur, opp_type):
#     mocker.patch.object(fcf_autotrageur, 'exchange1_basequote', ['BTC', 'USD'],
#         create=True)

#     fcf_autotrageur._FCFAutotrageur__set_message(opp_type)
#     if opp_type is SpreadOpportunity.LOW:
#         assert fcf_autotrageur.message == (
#                     EMAIL_LOW_SPREAD_HEADER
#                     + fcf_autotrageur.exchange1_basequote[0]
#                     + " is "
#                     + str(fcf_autotrageur.spread_opp[arbseeker.SPREAD]))
#     elif opp_type is SpreadOpportunity.HIGH:
#         assert fcf_autotrageur.message == (
#                     EMAIL_HIGH_SPREAD_HEADER
#                     + fcf_autotrageur.exchange1_basequote[0]
#                     + " is "
#                     + str(fcf_autotrageur.spread_opp[arbseeker.SPREAD]))
#     elif opp_type is None:
#         assert fcf_autotrageur.message == EMAIL_NONE_SPREAD
#     else:
#         pytest.fail('Unsupported spread opportunity type.')


# class TestExecuteTrade():

#     @pytest.mark.parametrize('is_network_err, is_abort_trade_err', [
#         (True, False),
#         (False, True),
#         (False, False)
#     ])
#     @pytest.mark.parametrize('is_dry_run, execute_cmd', [
#         (True, 'execute'),
#         (True, 'eggxecute'),
#         (True, ''),
#         (False, 'execute'),
#         (False, ''),
#         (False, 'eggxecute')
#     ])
#     def test_execute_trade(self, mocker, fcf_autotrageur, is_dry_run, execute_cmd,
#                            is_network_err, is_abort_trade_err):
        # mock_FCFAutotrageur__email_or_throttle = mocker.patch.object(fcf_autotrageur, '_FCFAutotrageur__email_or_throttle')
        # mock_exec_arb = mocker.patch.object(arbseeker, 'execute_arbitrage')
        # mocker.patch.dict(fcf_autotrageur.config, { 'dryrun': is_dry_run })
        # mock_input = mocker.patch('builtins.input', return_value=execute_cmd)

        # if is_network_err:
        #     mock_exec_arb.side_effect = NetworkError
        # elif is_abort_trade_err:
        #     mock_exec_arb.side_effect = arbseeker.AbortTradeException

        # fcf_autotrageur._execute_trade()
        # mock_FCFAutotrageur__email_or_throttle.assert_called_with(fcf_autotrageur.spread_opp[arbseeker.SPREAD])

        # if is_dry_run:
        #     mock_exec_arb.assert_called_with(fcf_autotrageur.spread_opp)
        #     mock_input.assert_not_called()
        # else:
        #     mock_input.assert_called_with("Type 'execute' to attempt trade execution\n")
        #     if execute_cmd == 'execute':
        #         mock_exec_arb.assert_called_with(fcf_autotrageur.spread_opp)
        #     else:
        #         mock_exec_arb.assert_not_called()


def test_clean_up(fcf_autotrageur):
    assert fcf_autotrageur.message == 'fake message'
    # assert fcf_autotrageur.spread_opp == { arbseeker.SPREAD: 1.0 }
    fcf_autotrageur._clean_up()
    assert fcf_autotrageur.message is None
    assert fcf_autotrageur.spread_opp is None
