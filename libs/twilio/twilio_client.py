import logging
import os
import urllib.parse

from twilio.rest import Client


TWILIO_ACTIVE_STATE = 'active'

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


def phone(messages, to_phone_numbers, from_phone_number):
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
    escaped_messages = _form_messages_url_query(messages)
    client = Client(os.getenv('ACCOUNT_SID'), os.getenv('AUTH_TOKEN'))

    for phone_number in to_phone_numbers:
        logging.debug('Phoning: {}'.format(phone_number))
        client.calls.create(
            url='http://twimlets.com/message?' + escaped_messages,
            to=phone_number,
            from_=from_phone_number)

def test_connection():
    account_sid = os.getenv('ACCOUNT_SID')
    auth_token = os.getenv('AUTH_TOKEN')
    client = Client(account_sid, auth_token)
    account = client.api.accounts(account_sid).fetch()

    if account.status != TWILIO_ACTIVE_STATE:
        raise TwilioInactiveAccountError('The Twilio account is not active, it'
            ' is: {}'.format(account.status))
