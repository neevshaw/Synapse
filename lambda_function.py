# send_email_simple.py
import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = "smtp.gmail.com"   # change to your provider
SMTP_PORT = 465                # 465 for SMTP_SSL, 587 for STARTTLS
USERNAME = os.getenv("username")
PASSWORD = os.getenv("password")

def lambda_handler(event, context):
    # --- Email details ---
    recipient = event.get("to")
    subject = event.get("subject")
    body = event.get("body")

    msg = EmailMessage()
    msg["From"] = USERNAME
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        # Send the email using SSL
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.login(USERNAME, PASSWORD)
            smtp.send_message(msg)

        return {
            "statusCode": 200,
            "body": f"Email sent successfully to {recipient}"
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "error": str(e)
        }