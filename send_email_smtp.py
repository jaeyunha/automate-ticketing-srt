"""
Cross-platform email sender using SMTP.

Works on macOS, Linux, and Windows. Requires these environment variables:
  SMTP_EMAIL    - sender email address (e.g., your Gmail)
  SMTP_PASSWORD - app password (for Gmail: https://myaccount.google.com/apppasswords)
  SMTP_HOST     - SMTP server (default: smtp.gmail.com)
  SMTP_PORT     - SMTP port (default: 587)
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email_smtp(to_email, subject, message):
    """Send email via SMTP. Returns True on success, False on failure."""
    sender = os.getenv("SMTP_EMAIL")
    password = os.getenv("SMTP_PASSWORD")
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))

    if not sender or not password:
        logging.warning("SMTP_EMAIL or SMTP_PASSWORD not set — skipping SMTP email")
        return False

    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())

        return True
    except Exception as e:
        logging.error(f"SMTP email failed: {e}")
        return False
