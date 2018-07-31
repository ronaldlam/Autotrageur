import logging
import os
import time
import urllib.parse

from twilio.rest import Client

import libs.logging.autotrageur_logging as bot_logging

TWIMLETS_MESSAGE_ENDPOINT = 'http://twimlets.com/message?'
TWILIO_HTTP_CLIENT = 'twilio.http_client'
TWILIO_ACTIVE_STATE = 'active'
TWILIO_SUSPENDED_STATE = 'suspended'
TWILIO_CLOSED_STATE = 'closed'


class TwilioLogContext:
    def __init__(self, parent_context, stream_info_to_warning=False):
        self.parent_context = parent_context
        self.stream_info_to_warning = stream_info_to_warning

    def __enter__(self):
        if self.stream_info_to_warning is True:
            self.old_stream_level = self.parent_context.stream_handler.level
            self.parent_context.stream_handler.level = logging.WARNING

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.stream_info_to_warning is True:
            self.parent_context.stream_handler.level = logging.INFO


class TwilioInactiveAccountError(Exception):
    """Thrown when a Twilio Account is not 'active'.  It can be 'suspended' or
    'closed'."""
    pass


def _form_messages_url_query(messages):
    """Forms the url-safe query string for a string of 'Messages'.

    Each message can refer to an audio file to <Play> or text block to <Say>
    in accordance with Twilio API.
    Please Refer to: https://www.twilio.com/labs/twimlets/message

    Args:
        messages (list[str]): A list of strings containing either a message to
            <Say> or a url for server hosting an audio file to <Play>.

    Returns:
        str: A url-safe query string to be used to append to an existing
            twimlets endpoint.
    """
    messages_query_str = '&'.join(
        urllib.parse.quote('Message[{}]={}'.format(i, message), safe='=')
        for i, message in enumerate(messages))
    return messages_query_str


class TwilioClient:
    def __init__(self, account_sid, auth_token, log_context):
        """Constructor.

        Initializes the twilio client with provided `account_sid` and
        `auth_token`.

        Args:
            account_sid (str): The TWILIO_ACCOUNT_SID associated with the
                Twilio account.
            auth_token (str): The TWILIO_AUTH_TOKEN associated with the
                Twilio account.
        """
        # root_logger = logging.getLogger()
        # twilio_logger = logging.getLogger(TWILIO_HTTP_CLIENT)
        # twilio_logger.setLevel(logging.DEBUG)
        # requests_logger = logging.getLogger('requests')
        # requests_logger.setLevel(logging.DEBUG)
        # requests_logger.handlers = []
        # requests_logger.addHandler(root_logger.handlers[0])
        # twilio_logger.handlers = []
        # twilio_logger.addHandler(logging_listener.handlers[1])
        # twilio_logger.addFilter(TwilioLogFilter())
        # twilio_logger.propagate = False
        self.log_context = log_context
        self.client = Client(account_sid, auth_token)

    def test_connection(self):
        """Tests the TwilioClient's connection to Twilio APIs.

        Requests for the account's information to see if status is 'active' to
        verify that the account can be reached, and is alive.

        Raises:
            TwilioInactiveAccountError: Thrown if the twilio api can be reached but
                the account status is not 'active'.
        """

        # Disable the http logging for this one call, to avoid interfering with
        # cmd overlap with an input prompt.
        # logging.getLogger(TWILIO_HTTP_CLIENT).setLevel(logging.WARNING)
        # bot_logging.stream_handler.setLevel(logging.WARNING)
        with TwilioLogContext(self.log_context, stream_info_to_warning=True):
            account = self.client.api.accounts(self.client.account_sid).fetch()
            time.sleep(0.1)
        # bot_logging.stream_handler.setLevel(logging.INFO)
        # logging.getLogger(TWILIO_HTTP_CLIENT).setLevel(logging.INFO)

        if account.status != TWILIO_ACTIVE_STATE:
            raise TwilioInactiveAccountError('The Twilio account is not active'
                ', it is: {}'.format(account.status))

    def phone(self, messages, to_phone_numbers, from_phone_number):
        """Phone recipients to deliver one or more messages.

        Calls every phone number from `to_phone_numbers` using a
        `from_phone_number` purchased from Twilio.

        Args:
            messages (list[str]): A list of strings containing either a message to
                <Say> or a url for server hosting an audio file to <Play>.
            to_phone_numbers (list[str]): A list of recipient phone numbers.
            from_phone_number (str): A phone number purchased from Twilio to be
                used as the caller number.
        """
        # escaped_messages = _form_messages_url_query(messages)

        # for phone_number in to_phone_numbers:
        #     logging.debug('Phoning: {}'.format(phone_number))
            # self.client.calls.create(
            #     url=TWIMLETS_MESSAGE_ENDPOINT + escaped_messages,
            #     to=phone_number,
            #     from_=from_phone_number)
