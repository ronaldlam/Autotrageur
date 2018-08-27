import logging
import os
import time
import urllib.parse

from twilio.rest import Client

import libs.logging.bot_logging as bot_logging

TWIMLETS_MESSAGE_ENDPOINT = 'http://twimlets.com/message?'
TWILIO_ACTIVE_STATE = 'active'
TWILIO_SUSPENDED_STATE = 'suspended'
TWILIO_CLOSED_STATE = 'closed'


class TwilioLogContext:
    """A context object for temporarily swapping a parent logger's state.
    Usage should be with the 'with' keyword:
        Ex. `with TwilioLogContext(logger, stream_info_to_warning=True):`

    Idea from official logging cookbook:
    https://docs.python.org/3/howto/logging-cookbook.html#using-a-context-manager-for-selective-logging
    """
    def __init__(self, parent_logger, stream_info_to_warning=False):
        """Constructor.

        Args:
            parent_logger (AutotrageurBackgroundLogger): The parent logger
                object containing the currently used logging context.
            stream_info_to_warning (bool, optional): If True, will change the
                `parent_logger.stream_handler` to logging.WARNING state.
                Defaults to False.
        """
        self.parent_logger = parent_logger
        self.stream_info_to_warning = stream_info_to_warning

    def __enter__(self):
        """Upon use with a `with` keyword, will swap any parent logging state
        with the new, desired logging state.
        """
        if self.stream_info_to_warning:
            self.old_stream_level = self.parent_logger.stream_handler.level
            self.parent_logger.stream_handler.level = logging.WARNING

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Upon exiting the code block of a `with` keyword, will reverse-swap
        the previous context with the swapped-in logging state from `__enter__`

        Args:
            exc_type (type(Exception)): The Exception type if an exception is
                thrown within the 'with' code block.
            exc_value (str): The Exception value if an exception is thrown
                within the 'with' code block.
            exc_traceback (traceback): The Exception traceback if an exception
                is thrown within the 'with' code block.
        """
        if self.stream_info_to_warning:
            self.parent_logger.stream_handler.level = self.old_stream_level
            self.old_stream_level = None


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
    def __init__(self, account_sid, auth_token, parent_logger):
        """Constructor.

        Initializes the twilio client with provided `account_sid` and
        `auth_token`.

        Args:
            account_sid (str): The TWILIO_ACCOUNT_SID associated with the
                Twilio account.
            auth_token (str): The TWILIO_AUTH_TOKEN associated with the
                Twilio account.
            parent_logger (AutotrageurBackgroundLogger): The
        """
        self.parent_logger = parent_logger
        self.client = Client(account_sid, auth_token)

    def test_connection(self):
        """Tests the TwilioClient's connection to Twilio APIs.

        Requests for the account's information to see if status is 'active' to
        verify that the account can be reached, and is alive.

        Raises:
            TwilioInactiveAccountError: Thrown if the twilio api can be reached but
                the account status is not 'active'.
        """
        with TwilioLogContext(self.parent_logger, stream_info_to_warning=True):
            account = self.client.api.accounts(self.client.account_sid).fetch()
            # Necessary to prevent api response from logging after leaving
            # context scope and interfering with input prompts.
            time.sleep(0.1)

        if account.status != TWILIO_ACTIVE_STATE:
            raise TwilioInactiveAccountError('The Twilio account is not active'
                ', it is: {}'.format(account.status))

    def phone(self, messages, to_phone_numbers, from_phone_number, is_mock_call=False):
        """Phone recipients to deliver one or more messages.

        Calls every phone number from `to_phone_numbers` using a
        `from_phone_number` purchased from Twilio.

        Args:
            messages (list[str]): A list of strings containing either a message to
                <Say> or a url for server hosting an audio file to <Play>.
            to_phone_numbers (list[str]): A list of recipient phone numbers.
            from_phone_number (str): A phone number purchased from Twilio to be
                used as the caller number.
            is_mock_call (bool): If True, does not dial any of the recipients and
                merely logs to output.  Defaults to False.
        """
        if is_mock_call:
            logging.debug("**Mock call - twilio_client::phone triggered from "
                "number: {} to numbers: {}".format(
                    from_phone_number,
                    to_phone_numbers))
            return

        escaped_messages = _form_messages_url_query(messages)

        for phone_number in to_phone_numbers:
            logging.debug('Phoning: {}'.format(phone_number))
            self.client.calls.create(
                url=TWIMLETS_MESSAGE_ENDPOINT + escaped_messages,
                to=phone_number,
                from_=from_phone_number)
