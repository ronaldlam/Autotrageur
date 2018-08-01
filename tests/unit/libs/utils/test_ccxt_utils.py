import time
from unittest.mock import MagicMock

import pytest
from ccxt import ExchangeError, NetworkError
from libs.utils.ccxt_utils import (DEFAULT_ARG_LIST, DEFAULT_KWARG_LIST,
                                   WAIT_SECONDS, RetryableError, RetryCounter,
                                   wrap_ccxt_retry)

MOCK_FUNC1 = MagicMock()
MOCK_FUNC1_RETURN = 'MOCK_FUNC1'
MOCK_FUNC2 = MagicMock()
MOCK_FUNC2_RETURN = 'MOCK_FUNC2'
MOCK_FUNC3 = MagicMock()
MOCK_FUNC3_RETURN = 'MOCK_FUNC3'
EMPTY_ARGS = [()]
EMPTY_KWARGS = [{}]
ONE_ARG = [('ONE')]
ONE_KWARG = [{ 'one': 'ONE' }]
TRIPLE_ARG = [('ONE'), ('TWO'), ('THIRD')]
TRIPLE_KWARG = [
{
     'one': 'ONE',
     '1': '1',
     'won': 1
},
{
     'two': 'TWO',
     '2': 2.22
},
{
     'three': 'THREE'
}]

# Retry scenarios.
SCENARIO_ONE = 'one'
SCENARIO_TWO = 'two'
SCENARIO_MAX = 'max'

@pytest.fixture(autouse=True, scope='module')
def setup_mock_func_returns():
    MOCK_FUNC1.return_value = MOCK_FUNC1_RETURN
    MOCK_FUNC2.return_value = MOCK_FUNC2_RETURN
    MOCK_FUNC3.return_value = MOCK_FUNC3_RETURN


@pytest.fixture(autouse=True, scope='function')
def reset_mocks():
    MOCK_FUNC1.reset_mock()
    MOCK_FUNC2.reset_mock()
    MOCK_FUNC3.reset_mock()


@pytest.fixture(scope='module')
def retry_counter():
    return RetryCounter()


class TestWrapCcxtRetry():
    @pytest.mark.parametrize("funclist, arglist, kwarglist, expected_returns", [
        ([], DEFAULT_ARG_LIST, DEFAULT_KWARG_LIST, []),  # Case represents default params.
        ([MOCK_FUNC1, MOCK_FUNC2], EMPTY_ARGS, EMPTY_KWARGS, [MOCK_FUNC1_RETURN, MOCK_FUNC2_RETURN]),
        ([MOCK_FUNC1], ONE_ARG, ONE_KWARG, [MOCK_FUNC1_RETURN]),
        ([MOCK_FUNC1, MOCK_FUNC2, MOCK_FUNC3], TRIPLE_ARG, DEFAULT_KWARG_LIST, [MOCK_FUNC1_RETURN, MOCK_FUNC2_RETURN, MOCK_FUNC3_RETURN]),
        ([MOCK_FUNC1, MOCK_FUNC2, MOCK_FUNC3], DEFAULT_ARG_LIST, TRIPLE_KWARG, [MOCK_FUNC1_RETURN, MOCK_FUNC2_RETURN, MOCK_FUNC3_RETURN]),
        ([MOCK_FUNC1, MOCK_FUNC2, MOCK_FUNC3], TRIPLE_ARG, TRIPLE_KWARG, [MOCK_FUNC1_RETURN, MOCK_FUNC2_RETURN, MOCK_FUNC3_RETURN])
    ])
    def test_wrap_ccxt_retry(self, funclist, arglist, kwarglist, expected_returns):
        func_returns = wrap_ccxt_retry(funclist, arglist=arglist, kwarglist=kwarglist)

        # Need this empty args/kwargs extension for testing purposes.
        if arglist == DEFAULT_ARG_LIST:
            arglist = DEFAULT_ARG_LIST * len(funclist)
        if kwarglist == DEFAULT_KWARG_LIST:
            kwarglist = DEFAULT_KWARG_LIST * len(funclist)

        for i in range(len(funclist)):
            funclist[i].assert_called_once_with(*arglist[i], **kwarglist[i])

        assert func_returns == expected_returns

    @pytest.mark.parametrize("scenario", [None, SCENARIO_ONE, SCENARIO_TWO, SCENARIO_MAX])
    def test_wrap_ccxt_retry_network_err(self, mocker, scenario):
        mock_time_sleep = mocker.patch('time.sleep')
        if scenario is SCENARIO_ONE:
            MOCK_FUNC1.side_effect = [NetworkError, MOCK_FUNC1_RETURN, NetworkError]
            func_returns = wrap_ccxt_retry([MOCK_FUNC1], arglist=ONE_ARG, kwarglist=ONE_KWARG)
            mock_time_sleep.assert_called_with(WAIT_SECONDS)
            assert MOCK_FUNC1.call_count == 2
            assert mock_time_sleep.call_count == 1
            assert func_returns == [MOCK_FUNC1_RETURN]
        elif scenario is SCENARIO_TWO:
            MOCK_FUNC1.side_effect = [NetworkError, NetworkError, MOCK_FUNC1_RETURN]
            func_returns = wrap_ccxt_retry([MOCK_FUNC1], arglist=ONE_ARG, kwarglist=ONE_KWARG)
            mock_time_sleep.assert_called_with(WAIT_SECONDS)
            assert MOCK_FUNC1.call_count == 3
            assert mock_time_sleep.call_count == 2
            assert func_returns == [MOCK_FUNC1_RETURN]
        elif scenario is SCENARIO_MAX:
            MOCK_FUNC1.side_effect = [NetworkError, NetworkError, NetworkError]
            with pytest.raises(NetworkError):
                wrap_ccxt_retry([MOCK_FUNC1], arglist=ONE_ARG, kwarglist=ONE_KWARG)
            mock_time_sleep.assert_called_with(WAIT_SECONDS)
            assert MOCK_FUNC1.call_count == 3
            assert mock_time_sleep.call_count == 3
        else:
            wrap_ccxt_retry([MOCK_FUNC1], arglist=ONE_ARG, kwarglist=ONE_KWARG)
            mock_time_sleep.assert_not_called()
            assert MOCK_FUNC1.call_count == 1

    @pytest.mark.parametrize("exc_type, raised_type", [
        (Exception, Exception),
        (ExchangeError, RetryableError),
        (KeyError, KeyError),
    ])
    def test_wrap_ccxt_retry_exception(self, mocker, exc_type, raised_type):
        MOCK_FUNC1.side_effect = exc_type
        with pytest.raises(raised_type):
            wrap_ccxt_retry([MOCK_FUNC1], arglist=ONE_ARG, kwarglist=ONE_KWARG)


class TestRetryCounter:
    COUNTER_MAX = 10

    def test_init(self):
        counter = RetryCounter()
        assert counter._counter == self.COUNTER_MAX

    @pytest.mark.parametrize(
        'internal_counter, expected_result',
        [(0, 1), (3, 4), (10, 10)])
    def test_increment(self, mocker, retry_counter, internal_counter,
                       expected_result):
        mocker.patch.object(retry_counter, '_counter', internal_counter)
        retry_counter.increment()
        assert retry_counter._counter == expected_result

    @pytest.mark.parametrize(
        'internal_counter, expected_counter, expected_return',
        [(0, -3, False), (3, 0, True), (10, 7, True)])
    def test_decrement(self, mocker, retry_counter, internal_counter,
                       expected_counter, expected_return):
        mocker.patch.object(retry_counter, '_counter', internal_counter)
        result = retry_counter.decrement()
        assert retry_counter._counter == expected_counter
        assert result == expected_return
