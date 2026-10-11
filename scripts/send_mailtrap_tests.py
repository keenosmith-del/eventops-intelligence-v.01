#!/usr/bin/env python3
"""Send the three prepared assessment messages to Mailtrap Email Testing once."""

import argparse
import getpass
import json
import smtplib
import ssl
import sys
import time
import warnings
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path


SMTP_HOST = "sandbox.smtp.mailtrap.io"
SMTP_PORT = 2525
PAYLOAD_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs/testing/mailtrap/final-assessment.json"
)


def load_messages():
    payloads = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
    if not isinstance(payloads, list) or len(payloads) != 3:
        raise ValueError("Expected exactly three prepared test messages.")

    messages = []
    for payload in payloads:
        sender = payload["from"]
        recipients = payload["to"]
        addresses = [sender["email"], *(item["email"] for item in recipients)]
        if not recipients or any(
            address.rsplit("@", 1)[-1].lower() != "example.com"
            for address in addresses
        ):
            raise ValueError("Only the prepared example.com test addresses are allowed.")
        message = EmailMessage()
        message["From"] = formataddr((sender.get("name", ""), sender["email"]))
        message["To"] = ", ".join(
            formataddr((item.get("name", ""), item["email"]))
            for item in recipients
        )
        message["Subject"] = payload["subject"]
        message.set_content(payload["text"])
        messages.append(message)
    return messages


def describe_error(error):
    """Expose useful diagnostics without echoing arbitrary provider content."""
    details = type(error).__name__
    code = getattr(error, "smtp_code", None)
    if isinstance(code, int):
        details += f" (SMTP {code})"
    response = getattr(error, "smtp_error", b"")
    if isinstance(response, bytes):
        response = response.decode("utf-8", errors="replace")
    response = str(response).lower()
    reasons = (
        ("too many emails", "Sandbox sending rate limit reached."),
        ("rate limit", "Sandbox sending rate limit reached."),
        ("monthly", "Sandbox monthly allowance reached."),
        ("too many connections", "SMTP connection limit reached."),
        ("message too big", "Message size limit reached."),
    )
    for fragment, reason in reasons:
        if fragment in response:
            return f"{details}: {reason}"
    if isinstance(error, smtplib.SMTPAuthenticationError):
        return f"{details}: Sandbox authentication rejected."
    if isinstance(error, smtplib.SMTPRecipientsRefused):
        return f"{details}: Sandbox rejected the recipient."
    if isinstance(error, (TimeoutError, ConnectionError, OSError)):
        return f"{details}: Connection, TLS, or local file operation failed."
    return f"{details}: Operation failed; raw exception text withheld for credential safety."


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--start-at", type=int, choices=(1, 2, 3), default=1,
        help="First message to submit (1–3). Earlier messages are skipped entirely.",
    )
    args = parser.parse_args(argv)
    sent = 0
    stage = "loading assessment payloads"
    current = None
    try:
        messages = load_messages()
        print("Destination: Mailtrap Email Testing sandbox.smtp.mailtrap.io:2525")
        print(f"Submitting messages {args.start_at}–3; no automatic retries.")
        stage = "reading sandbox credentials"
        username = input("Sandbox SMTP username: ").strip()
        # Refuse an echoing fallback if this is run without a usable terminal.
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            password = getpass.getpass("Sandbox SMTP password: ")
        if not username or not password:
            raise ValueError("Both sandbox SMTP credentials are required.")

        stage = "connecting to sandbox SMTP"
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
            smtp.ehlo()
            stage = "establishing TLS"
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
            stage = "authenticating to sandbox SMTP"
            smtp.login(username, password)
            del username, password
            for index in range(args.start_at - 1, len(messages)):
                if sent:
                    stage = "waiting between submissions"
                    time.sleep(11)
                current = index + 1
                message = messages[index]
                stage = f"submitting message {current}"
                refused = smtp.send_message(message)
                if refused:
                    raise smtplib.SMTPRecipientsRefused(refused)
                sent += 1
                print(f"Sent {current}/3: {message['Subject']}")
            stage = "closing SMTP connection (all selected messages accepted)"
        print(f"All {sent} selected messages submitted to Mailtrap Email Testing.")
        return 0
    except (Exception, KeyboardInterrupt) as error:
        # Provider exception text may contain authentication details: never print it.
        print(
            f"Stopped while {stage}: {describe_error(error)}\n"
            f"Confirmed submissions this invocation: {sent}. "
            "No automatic retries were made. Check the sandbox inbox before "
            "rerunning; a connection failure during submission can leave acceptance uncertain.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
