"""SMTP email sender tool."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import List


class EmailSender:
    """Sends transactional emails via SMTP."""

    def __init__(self) -> None:
        self.host = os.getenv("SMTP_HOST", "localhost")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.username = os.getenv("SMTP_USERNAME")
        self.password = os.getenv("SMTP_PASSWORD")
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    def send(
        self,
        *,
        subject: str,
        body: str,
        sender: str,
        recipients: List[str],
    ) -> None:
        if not recipients:
            raise ValueError("At least one recipient is required")

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = sender
        message["To"] = ", ".join(recipients)
        message.set_content(body)

        with smtplib.SMTP(self.host, self.port) as server:
            if self.use_tls:
                server.starttls()
            if self.username and self.password:
                server.login(self.username, self.password)
            server.send_message(message)


if __name__ == "__main__":
    demo_recipient = os.getenv("DEMO_EMAIL_RECIPIENT")
    if not demo_recipient:
        print("Set DEMO_EMAIL_RECIPIENT to run the email sender demo.")
    else:
        sender = EmailSender()
        sender.send(
            subject="APAS test",
            body="This is a test message from APAS.",
            sender=os.getenv("SMTP_FROM", "apas@example.com"),
            recipients=[demo_recipient],
        )
        print("Email queued for delivery")
