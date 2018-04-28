from unittest.mock import Mock, MagicMock, patch

import pytest
from pytest_mock import mocker

import smtplib
import yaml

from libs.email_client import simple_email_client


MOCK_GMAIL_ONE_RECIPIENT = "tests/libs/email_client/mockdata/mock_gmail_one_recipient.yaml"
MOCK_GMAIL_MULTIPLE_RECIPIENTS = "tests/libs/email_client/mockdata/mock_gmail_multiple_recipients.yaml"
MOCK_GMAIL_BAD_FORMAT = "tests/libs/email_client/mockdata/mock_gmail_bad_format.yaml"
MOCK_NON_EXISTENT_FILE = "does/not/exist.yaml"


@pytest.mark.parametrize('email_yaml', [
    pytest.param(MOCK_GMAIL_BAD_FORMAT, marks=pytest.mark.xfail(raises=yaml.scanner.ScannerError, strict=True)),
    pytest.param(MOCK_NON_EXISTENT_FILE, marks=pytest.mark.xfail(raises=FileNotFoundError, strict=True)),
    MOCK_GMAIL_ONE_RECIPIENT,
    MOCK_GMAIL_MULTIPLE_RECIPIENTS
])
def test_extract_email_info(email_yaml):
    email_cfg = simple_email_client._extract_email_info(email_yaml)
    assert isinstance(email_cfg, dict)

test_send_single_email_params = [
    # Good case
    ('testemail@gmail.com', {
        'host':'fakehost',
        'port': 'fakeport',
        'username': 'fakeusername',
        'password': 'fakepassword'
    }, 'message'),
    # Missing key 'host'
    pytest.param('testemail@gmail.com', {
        'port': 'fakeport',
        'username': 'fakeusername',
        'password': 'fakepassword'
    }, 'message', marks=pytest.mark.xfail(raises=KeyError, strict=True)),
    # Missing key 'port'
    pytest.param('testemail@gmail.com', {
        'hort':'fakehost',
        'username': 'fakeusername',
        'password': 'fakepassword'
    }, 'message', marks=pytest.mark.xfail(raises=KeyError, strict=True)),
    # Missing key 'username'
    pytest.param('testemail@gmail.com', {
        'hort':'fakehost',
        'port': 'fakeport',
        'password': 'fakepassword'
    }, 'message', marks=pytest.mark.xfail(raises=KeyError, strict=True)),
    # Missing key 'password'
    pytest.param('testemail@gmail.com', {
        'hort':'fakehost',
        'port': 'fakeport',
        'username': 'fakeusername',
    }, 'message', marks=pytest.mark.xfail(raises=KeyError, strict=True))
]

@pytest.mark.parametrize('recipient, email_cfg, msg',
    test_send_single_email_params)
def test_send_single_email(mocker, recipient, email_cfg, msg):
    MockSMTP = mocker.patch('smtplib.SMTP', autospec=True)
    # The return_value of the Mock class is the mock instance used.
    mock_smtp_server = MockSMTP.return_value

    simple_email_client.send_single_email(recipient, email_cfg, msg)
    MockSMTP.assert_called_with(email_cfg['host'], email_cfg['port'])
    mock_smtp_server.ehlo.assert_called_with()
    mock_smtp_server.starttls.assert_called_with()
    mock_smtp_server.login.assert_called_with(email_cfg['username'], email_cfg['password'])
    mock_smtp_server.sendmail.assert_called_with(email_cfg['username'], recipient, msg)
    mock_smtp_server.quit.assert_called_with()


def test_send_all_emails(mocker):
    mock_return_extract_email = {
        'host':'fakehost',
        'port': 'fakeport',
        'username': 'fakeusername',
        'password': 'fakepassword',
        'recipients': ['fakeemail@gmail.com']
    }
    mock_extract_email_info = mocker.patch.object(simple_email_client,
         '_extract_email_info',
         return_value=mock_return_extract_email)
    mock_send_single_email = mocker.patch.object(simple_email_client, 'send_single_email')

    simple_email_client.send_all_emails(MOCK_GMAIL_ONE_RECIPIENT, "message")
    mock_extract_email_info.assert_called_with(MOCK_GMAIL_ONE_RECIPIENT)
    mock_send_single_email.assert_called()
