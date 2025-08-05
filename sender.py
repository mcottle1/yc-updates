import os
import smtplib
from email.message import EmailMessage

try:
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
except ValueError:
    raise ValueError("SMTP_PORT must be an integer")

EMAIL_ADDRESS = 'ycombinatorupdates@gmail.com'
EMAIL_PASSWORD = 'emvj zttd sqpr emmm'

RECIPIENTS = [
    "mhill@pelionvp.com"
]

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
        print(f"Email sent to {RECIPIENTS}")
