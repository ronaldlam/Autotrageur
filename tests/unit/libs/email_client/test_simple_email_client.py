import smtplib
from email.message import EmailMessage

import pytest
import yaml

from libs.email_client import simple_email_client

MOCK_GMAIL_ONE_RECIPIENT = "tests/unit/libs/email_client/mockdata/mock_gmail_one_recipient.yaml"
MOCK_GMAIL_MULTIPLE_RECIPIENTS = "tests/unit/libs/email_client/mockdata/mock_gmail_multiple_recipients.yaml"
MOCK_GMAIL_BAD_FORMAT = "tests/unit/libs/email_client/mockdata/mock_gmail_bad_format.yaml"
MOCK_NON_EXISTENT_FILE = "does/not/exist.yaml"
MOCK_SUBJECT = 'subject: subject'
MOCK_BODY = 'mock body'
MOCK_EMAIL_MESSAGE_OBJ = EmailMessage()

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
    }, MOCK_EMAIL_MESSAGE_OBJ),
    # Missing key 'host'
    pytest.param('testemail@gmail.com', {
        'port': 'fakeport',
        'username': 'fakeusername',
        'password': 'fakepassword'
    }, MOCK_EMAIL_MESSAGE_OBJ, marks=pytest.mark.xfail(raises=KeyError, strict=True)),
    # Missing key 'port'
    pytest.param('testemail@gmail.com', {
        'hort':'fakehost',
        'username': 'fakeusername',
        'password': 'fakepassword'
    }, MOCK_EMAIL_MESSAGE_OBJ, marks=pytest.mark.xfail(raises=KeyError, strict=True)),
    # Missing key 'username'
    pytest.param('testemail@gmail.com', {
        'hort':'fakehost',
        'port': 'fakeport',
        'password': 'fakepassword'
    }, MOCK_EMAIL_MESSAGE_OBJ, marks=pytest.mark.xfail(raises=KeyError, strict=True)),
    # Missing key 'password'
    pytest.param('testemail@gmail.com', {
        'hort':'fakehost',
        'port': 'fakeport',
        'username': 'fakeusername',
    }, MOCK_EMAIL_MESSAGE_OBJ, marks=pytest.mark.xfail(raises=KeyError, strict=True))
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
    mock_smtp_server.send_message.assert_called_with(msg)
    mock_smtp_server.quit.assert_called_with()


@pytest.mark.parametrize('config_file_path', [
    MOCK_GMAIL_ONE_RECIPIENT, MOCK_GMAIL_MULTIPLE_RECIPIENTS
])
def test_send_all_emails(mocker, config_file_path):
    mocker.spy(simple_email_client, '_extract_email_info')
    mock_send_single_email = mocker.patch.object(
        simple_email_client, 'send_single_email')
    mock_construct_email_msg = mocker.patch.object(
        simple_email_client, '_construct_email_msg',
        return_value=MOCK_EMAIL_MESSAGE_OBJ)

    email_cfg = simple_email_client._extract_email_info(config_file_path)
    simple_email_client.send_all_emails(
        config_file_path, MOCK_SUBJECT, MOCK_BODY)

    expected_construct_email_call_args_list = []
    expected_send_single_email_call_args_list = []
    simple_email_client._extract_email_info.assert_called_with(config_file_path)    # pylint: disable=E1101
    for recipient in email_cfg['recipients']:
        expected_construct_email_call_args_list.append(mocker.call(
            MOCK_SUBJECT, MOCK_BODY, email_cfg['username'], recipient
        ))
        expected_send_single_email_call_args_list.append(mocker.call(
            recipient, email_cfg, MOCK_EMAIL_MESSAGE_OBJ
        ))

    assert mock_construct_email_msg.call_args_list == expected_construct_email_call_args_list
    assert mock_send_single_email.call_args_list == expected_send_single_email_call_args_list
    assert mock_send_single_email.call_count == len(email_cfg['recipients'])
