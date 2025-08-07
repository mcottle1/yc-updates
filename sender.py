import os
import smtplib
from email.message import EmailMessage

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
    raise ValueError("EMAIL_ADDRESS and EMAIL_PASSWORD environment variables must be set")

recipients_string = os.environ.get('EMAIL_RECIPIENTS')
if not recipients_string:
    raise ValueError("EMAIL_RECIPIENTS environment variable must be set")

cc_recipients_string = os.environ.get('EMAIL_CC_RECIPIENTS')
if not cc_recipients_string:
    raise ValueError("EMAIL_CC_RECIPIENTS environment variable must be set")

print(cc_recipients_string)

RECIPIENTS = [email.strip() for email in recipients_string.split(',')]
CC_RECIPIENTS = [email.strip() for email in cc_recipients_string.split(',')] if cc_recipients_string else []

def send_email(subject: str, body: str, html_body: str):
    msg = EmailMessage()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ', '.join(RECIPIENTS)
    if CC_RECIPIENTS:
        msg['Cc'] = ', '.join(CC_RECIPIENTS)
    msg['Subject'] = subject
    msg.set_content(body)
    msg.add_alternative(html_body, subtype='html')

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls() 
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        all_recipients = RECIPIENTS[:]
        if CC_RECIPIENTS:
            all_recipients.extend(CC_RECIPIENTS)
        smtp.send_message(msg, to_addrs=all_recipients)
        print(f"Email sent")
