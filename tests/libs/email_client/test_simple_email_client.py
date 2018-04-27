from unittest.mock import Mock, MagicMock, patch

import pytest

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


@patch('smtplib.SMTP', autospec=True)
def test_send_single_mail(MockSMTP):
    fake_cfg = {
        'host':'fakehost',
        'port': 'fakeport',
        'username': 'fakeusername',
        'password': 'fakepassword'
    }
    fake_email = 'testemail@gmail.com'
    fake_message = 'message'

    # The return_value of the Mock class is the mock instance used.
    mock_smtp_server = MockSMTP.return_value

    simple_email_client.send_single_email(fake_email, fake_cfg, fake_message)
    MockSMTP.assert_called_with(fake_cfg['host'], fake_cfg['port'])
    mock_smtp_server.ehlo.assert_called_with()
    mock_smtp_server.starttls.assert_called_with()
    mock_smtp_server.login.assert_called_with(fake_cfg['username'], fake_cfg['password'])
    mock_smtp_server.sendmail.assert_called_with(fake_cfg['username'], fake_email, fake_message)
    mock_smtp_server.quit.assert_called_with()