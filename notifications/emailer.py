"""
Email notification sender.

Supports two backends:
- SMTP  (set EMAIL_BACKEND=smtp, or leave unset — default)
- Resend (set EMAIL_BACKEND=resend)

Required env vars are documented in .env.example.
"""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

from scrapers.base import Job
from notifications.templates import render_html, render_text

logger = logging.getLogger(__name__)


def send_notifications(jobs: list[Job]) -> None:
    if not jobs:
        logger.info("No new jobs to notify about")
        return

    backend = os.getenv("EMAIL_BACKEND", "smtp").lower()
    subject = f"New Sports Tech Jobs ({len(jobs)})"
    html_body = render_html(jobs)
    text_body = render_text(jobs)

    if backend == "resend":
        _send_resend(subject, html_body, text_body)
    else:
        _send_smtp(subject, html_body, text_body)


def _send_smtp(subject: str, html_body: str, text_body: str) -> None:
    host = os.environ["SMTP_HOST"]
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASSWORD"]
    from_addr = os.getenv("EMAIL_FROM", user)
    to_addr = os.environ["EMAIL_TO"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(host, port) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.sendmail(from_addr, [to_addr], msg.as_string())

    logger.info("Email sent via SMTP", extra={"to": to_addr, "subject": subject})


def _send_resend(subject: str, html_body: str, text_body: str) -> None:
    api_key = os.environ["RESEND_API_KEY"]
    from_addr = os.environ["EMAIL_FROM"]
    to_addr = os.environ["EMAIL_TO"]

    response = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "from": from_addr,
            "to": [to_addr],
            "subject": subject,
            "html": html_body,
            "text": text_body,
        },
        timeout=10,
    )
    response.raise_for_status()
    logger.info("Email sent via Resend", extra={"to": to_addr, "subject": subject})
