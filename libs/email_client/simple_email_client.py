import logging
import smtplib
from email.message import EmailMessage

import yaml


def _construct_email_msg(subject, body, from_addr, to_addr):
    """Constructs an EmailMessage to be used in sending an e-mail.

    Args:
        subject (str): The subject of the message.
        body (str): The body (main content) of the e-mail to be sent.
        from_addr (str): Sender's e-mail address.
        to_addr (str): Recipient's e-mail address.

    Returns:
        EmailMessage: An EmailMessage object containing all information
            needed to send an email.
    """
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg.set_content(body)
    return msg


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
        email_cfg = yaml.safe_load(ymlfile)

    return email_cfg


def send_single_email(recipient, email_cfg, msg):
    """Sends an e-mail to a single recipient.

    Args:
        recipient (str): A recipient's e-mail address.
        email_cfg (dict[]): A dictionary of e-mail configuration properties.
        msg (EmailMessage): An EmailMessage object containing all information
            needed to send an email.

    Raises:
        SMTPResponseException: If an SMTP error occurs containing 'smtp_code'
            and 'smtp_error'.
        SMTPException: The SMTP base error exception.
        Exception: Generic Exception thrown if non-SMTP related.
    """
    smtp_server = None
    try:
        smtp_server = smtplib.SMTP(email_cfg['host'], email_cfg['port'])
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.login(email_cfg['username'], email_cfg['password'])

        smtp_server.send_message(msg)
        logging.info("Email sent successfully to: %s", recipient)
    except smtplib.SMTPResponseException:
        errcode = getattr(smtp_ex, 'smtp_code')
        errmsg = getattr(smtp_ex, 'smtp_error')
        logging.error("SMTPResponseException encountered with smpt_code: %s "
                      "and smtp_error: %s", str(errcode), errmsg)
        raise
    except smtplib.SMTPException as smtp_ex:
        logging.error("SMTPException encountered trying to send email: %s",
                      smtp_ex)
        raise
    except Exception as e:
        logging.error("Exception encountered trying to send email: %s", e)
        raise
    finally:
        if smtp_server:
            smtp_server.quit()


def send_all_emails(email_cfg_path, subject, body):
    """Sends an e-mail message to one or more e-mails.

    Args:
        email_cfg_path (str): Path to e-mail configuration for sending emails.
        subject (str): The subject of the message.
        body (str): The body (main content) of the e-mail to be sent.
    """
    email_cfg = _extract_email_info(email_cfg_path)

    for recipient in email_cfg['recipients']:
        msg = _construct_email_msg(
            subject, body, email_cfg['username'], recipient)
        send_single_email(recipient, email_cfg, msg)
