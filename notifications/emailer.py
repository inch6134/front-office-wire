"""
Email notification sender.

Supports:
- SMTP  (set EMAIL_BACKEND=smtp, or leave unset — default)

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
