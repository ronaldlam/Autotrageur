import logging
import smtplib

import yaml

EMAIL_CONFIG_FILEPATH = "configs/email_info.yaml"
LOGGER = logging.getLogger()


def _extract_email_info(email_cfg_path):
    """Extracts e-mail configuration information from the e-mail_info file.

    Args:
        email_cfg_path (file): Path to a .yaml file containing email
            info.

    Returns:
        dict[]: A dict of email configuration key/value pairs.  Ex:

        {'username': 'examplemail@gmail.com',
         'password': 'some_great_safe_pw',
         'host': 'smtp.gmail.com',
         'port': 587
         'fail_silent': False
         'recipients': ['example1@gmail.com',
                        'example2@gmail.com',
                        'example3@gmail.com']
        }
    """
    with open(email_cfg_path, "r") as ymlfile:
        email_cfg = yaml.load(ymlfile)

    return email_cfg


def send_single_email(recipient, email_cfg, msg):
    """Sends an e-mail to a single recipient.

    Args:
        recipient (str): A recipient's e-mail address.
        email_cfg (dict[]): A dictionary of e-mail configuration properties.
        msg (str): A message formatted to be written as an e-mail (non-MIME).
    """
    smtp_server = smtplib.SMTP(email_cfg['host'], email_cfg['port'])

    try:
        # The SMTP server you're connecting to requires a sort of 'handshake'
        # for the service to work properly. This is done using the .ehlo()
        # function of smtplib.
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.login(email_cfg['username'], email_cfg['password'])

        smtp_server.sendmail(email_cfg['username'], recipient, msg)
        LOGGER.info("Email sent successfully to: %s", recipient)
    except Exception as ex:
        LOGGER.error("Error encountered trying to send email: %s", ex)
    finally:
        smtp_server.quit()


def send_all_emails(email_cfg_path, msg):
    """Sends an e-mail message to one or more e-mails.

    Args:
        email_cfg_path (str): Path to e-mail configuration for sending emails.
        msg (str): An message formatted to be sent as an e-mail (non-MIME).
    """
    email_cfg = _extract_email_info(email_cfg_path)

    for recipient in email_cfg['recipients']:
        send_single_email(recipient, email_cfg, msg)
