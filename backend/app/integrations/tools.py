"""Read-only HTTPS tools. No fixtures, sending, browser execution or model calls."""

import ipaddress
import os
import socket
import time
from urllib.parse import urlsplit, urlunsplit

import httpx

MAX_BYTES = 512_000
DEFAULT_CALENDAR = "https://www.officeholidays.com/ics/south-africa"
DEFAULT_WEB = "https://date.nager.at/api/v3/PublicHolidays/2026/ZA"


class ToolError(Exception):
    pass


class NotConnected(ToolError):
    pass


def safe_reference(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def validate_url(url: str):
    parts = urlsplit(url)
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.username
        or parts.password
        or parts.port not in (None, 443)
    ):
        raise ToolError(
            "Source must be a public HTTPS URL without embedded credentials."
        )
    try:
        addresses = socket.getaddrinfo(parts.hostname, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ToolError("Source hostname could not be resolved.") from exc
    if any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ToolError("Private and local network sources are not allowed.")


def fetch_text(url: str, *, headers=None, transport=None) -> str:
    validate_url(url)
    started = time.monotonic()
    try:
        with httpx.Client(
            timeout=httpx.Timeout(12, connect=5),
            follow_redirects=False,
            transport=transport,
        ) as client:
            with client.stream(
                "GET",
                url,
                headers={"User-Agent": "EventOps-Assessment/0.1", **(headers or {})},
            ) as response:
                if response.status_code >= 300:
                    raise ToolError(
                        f"Source returned HTTP {response.status_code}. No redirects or fallback were followed."
                    )
                chunks = []
                size = 0
                for chunk in response.iter_bytes():
                    if time.monotonic() - started > 20:
                        raise ToolError(
                            "Source exceeded the bounded streaming read window."
                        )
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise ToolError("Source exceeds the 512 KB read limit.")
                    chunks.append(chunk)
                return b"".join(chunks).decode("utf-8", errors="replace")
    except httpx.HTTPError as exc:
        raise ToolError(
            "HTTPS source request failed or timed out. No retry was performed."
        ) from exc


def connection_info() -> list[dict]:
    info = []
    for key, label, env, default in [
        ("calendar", "Remote iCalendar", "CALENDAR_FEED_URL", DEFAULT_CALENDAR),
        ("web", "HTTPS reference data", "WEB_SOURCE_URL", DEFAULT_WEB),
    ]:
        url = os.getenv(env, default)
        info.append(
            {
                "id": key,
                "label": label,
                "status": "configured" if url else "not_connected",
                "source": safe_reference(url) if url else None,
                "note": "Configured source; connectivity is confirmed only by an executed run.",
            }
        )
    available = all(
        os.getenv(k)
        for k in ["MAILTRAP_API_TOKEN", "MAILTRAP_ACCOUNT_ID", "MAILTRAP_INBOX_ID"]
    )
    info.append(
        {
            "id": "email",
            "label": "Mailtrap Email Sandbox (read only)",
            "status": "configured" if available else "not_connected",
            "source": "https://mailtrap.io" if available else None,
            "note": "Requires MAILTRAP_API_TOKEN, MAILTRAP_ACCOUNT_ID and MAILTRAP_INBOX_ID. Only a dedicated synthetic-data sandbox is read.",
        }
    )
    return info


def read_calendar(limit: int, transport=None) -> dict:
    url = os.getenv("CALENDAR_FEED_URL", DEFAULT_CALENDAR)
    if not url:
        raise NotConnected("Calendar feed URL is not configured.")
    return {
        "source_type": "calendar",
        "source_reference": safe_reference(url),
        "body": fetch_text(url, transport=transport),
        "limit": limit,
    }


def read_web(limit: int, transport=None) -> dict:
    url = os.getenv("WEB_SOURCE_URL", DEFAULT_WEB)
    if not url:
        raise NotConnected("Web source URL is not configured.")
    return {
        "source_type": "web",
        "source_reference": safe_reference(url),
        "body": fetch_text(url, transport=transport),
        "limit": limit,
    }


def read_email(limit: int, transport=None) -> dict:
    token = os.getenv("MAILTRAP_API_TOKEN")
    account = os.getenv("MAILTRAP_ACCOUNT_ID")
    inbox = os.getenv("MAILTRAP_INBOX_ID")
    if not all([token, account, inbox]):
        raise NotConnected(
            "Mailtrap sandbox is not connected. Configure the three server-side Mailtrap variables."
        )
    if not account.isdigit() or not inbox.isdigit():
        raise ToolError("Mailtrap account and inbox identifiers must be numeric.")
    import json

    root = f"https://mailtrap.io/api/accounts/{account}/inboxes/{inbox}/messages"
    headers = {"Api-Token": token}
    try:
        items = json.loads(fetch_text(root, headers=headers, transport=transport))
        if not isinstance(items, list):
            raise ValueError("Expected list")
        messages = []
        for item in items[: min(limit, 3)]:
            message_id = str(item["id"])
            if not message_id.isdigit():
                raise ValueError("Invalid message ID")
            url = f"{root}/{message_id}/body.txt"
            messages.append(
                {
                    "id": message_id,
                    "subject": str(item.get("subject", ""))[:500],
                    "body": fetch_text(url, headers=headers, transport=transport)[
                        :10000
                    ],
                    "source_reference": url,
                }
            )
    except (ValueError, KeyError, TypeError) as exc:
        raise ToolError("Mailtrap returned an invalid message response.") from exc
    return {
        "source_type": "email",
        "source_reference": root,
        "messages": messages,
        "limit": limit,
    }
