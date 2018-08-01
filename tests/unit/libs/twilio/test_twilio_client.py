from unittest.mock import MagicMock

import pytest

import libs.twilio.twilio_client as twilio_client
from libs.twilio.twilio_client import (TWILIO_ACTIVE_STATE,
                                       TWILIO_CLOSED_STATE,
                                       TWILIO_SUSPENDED_STATE,
                                       TWIMLETS_MESSAGE_ENDPOINT, TwilioClient,
                                       TwilioInactiveAccountError)

FAKE_ACCOUNT_SID = 'fake_account_sid'
FAKE_AUTH_TOKEN = 'fake_auth_token'

# Mock the Client object from the Twilio API Library.
twilio_client.Client = MagicMock()

@pytest.fixture(scope='module')
def mock_twilio_client():
    mock_twilio_client = TwilioClient(FAKE_ACCOUNT_SID, FAKE_AUTH_TOKEN)
    return mock_twilio_client

@pytest.mark.parametrize('messages, expected_query_str', [
    (['a msg'], 'Message%5B0%5D=a%20msg'),
    (['msg 1', 'a msg 2'], 'Message%5B0%5D=msg%201&Message%5B1%5D=a%20msg%202'),
    ([
        'a msg',
        'Traceback (most recent call last):\\nFile "C:\\folder\\Autotrageur\\bot\\arbitrage\\autotrageur.py", '
        'line 999, in _some_method\\nraise Exception("TEST EXCEPTION MESSAGE")'
    ], 'Message%5B0%5D=a%20msg&Message%5B1%5D=Traceback%20%28most%20recent%20call'
       '%20last%29%3A%5CnFile%20%22C%3A%5Cfolder%5CAutotrageur%5Cbot%5Carbitrage%5C'
       'autotrageur.py%22%2C%20line%20999%2C%20in%20_some_method%5Cnraise%20Exception'
       '%28%22TEST%20EXCEPTION%20MESSAGE%22%29'),
    (['=msg with=equals='], 'Message%5B0%5D==msg%20with=equals=')    # Note: The double '==' does not cause errors with the Twilio API as of 7/27/2018
])
def test_form_messages_url_query(mocker, messages, expected_query_str):
    url_safe_string = twilio_client._form_messages_url_query(messages)
    assert url_safe_string == expected_query_str


class TestTwilioClient:
    def test_init(self):
        test_twilio_client = TwilioClient(FAKE_ACCOUNT_SID, FAKE_AUTH_TOKEN)
        twilio_client.Client.assert_called_once_with(FAKE_ACCOUNT_SID, FAKE_AUTH_TOKEN)
        assert test_twilio_client.client is not None

        # From being mocked out in test module
        assert isinstance(test_twilio_client.client, MagicMock)

    @pytest.mark.parametrize('status', [
        TWILIO_ACTIVE_STATE,
        TWILIO_CLOSED_STATE,
        TWILIO_SUSPENDED_STATE
    ])
    def test_test_connection(self, mocker, mock_twilio_client, status):
        api_account_return = mocker.MagicMock()
        fetched_api_account = mocker.MagicMock()
        mocker.patch.object(mock_twilio_client.client, 'api')
        mocker.patch.object(mock_twilio_client.client, 'account_sid', FAKE_ACCOUNT_SID)
        mocker.patch.object(mock_twilio_client.client.api, 'accounts', return_value=api_account_return)
        mocker.patch.object(api_account_return, 'fetch', return_value=fetched_api_account)
        mocker.patch.object(fetched_api_account, 'status', status)

        if status is not TWILIO_ACTIVE_STATE:
            with pytest.raises(TwilioInactiveAccountError):
                mock_twilio_client.test_connection()
        else:
            mock_twilio_client.test_connection()

        mock_twilio_client.client.api.accounts.assert_called_once_with(FAKE_ACCOUNT_SID)
        api_account_return.fetch.assert_called_once_with()


    @pytest.mark.parametrize('to_phone_numbers', [
        [],
        ['+1234'],
        ['+1234', '+123456', '+12345678']
    ])
    def test_phone(self, mocker, mock_twilio_client, to_phone_numbers):
        FAKE_FROM_NUMBER = 'fake_from_number'
        ESCAPED_MESSAGES = 'bunchofescapedmessages'

        mocker.patch.object(twilio_client, '_form_messages_url_query', return_value=ESCAPED_MESSAGES)
        mocker.patch.object(mock_twilio_client.client, 'calls')
        mock_create_call = mocker.patch.object(mock_twilio_client.client.calls, 'create')

        mock_twilio_client.phone(['FAKE_MESSAGE'], to_phone_numbers, FAKE_FROM_NUMBER)

        expected_call_args_list = []
        for phone_number in to_phone_numbers:
            expected_call_args_list.append(mocker.call(
                url=TWIMLETS_MESSAGE_ENDPOINT + ESCAPED_MESSAGES,
                to=phone_number,
                from_=FAKE_FROM_NUMBER))
        twilio_client._form_messages_url_query.assert_called_once_with(['FAKE_MESSAGE'])    # pylint: disable=E1101
        assert mock_create_call.call_args_list == expected_call_args_list
