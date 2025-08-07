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

RECIPIENTS = [email.strip() for email in recipients_string.split(',')]

def send_email(subject: str, body: str, html_body: str):
    msg = EmailMessage()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ', '.join(RECIPIENTS)
    msg['Subject'] = subject
    msg.set_content(body)
    msg.add_alternative(html_body, subtype='html')

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls() 
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)
        print(f"Email sent")
