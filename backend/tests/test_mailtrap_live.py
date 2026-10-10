"""One opt-in, real Mailtrap-to-PostgreSQL probe. Never sends an email."""

import os
from pathlib import Path

import httpx
import pytest
from app.agents.workflow import execute
from app.integrations.tools import NotConnected, ToolError, read_email
from app.services import agent_repository as store
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
SUBJECT = "EventOps controlled verification | EVT-101 | MAILTRAP-EVT101-001"


class BoundedMailtrapTransport(httpx.BaseTransport):
    """Real TLS transport with a two-GET ceiling; no retries or other hosts."""

    def __init__(self, account, inbox):
        self.path = f"/api/accounts/{account}/inboxes/{inbox}/messages"
        self.calls = 0
        self.inner = None

    def handle_request(self, request):
        path = request.url.path
        allowed = path == self.path or (
            path.startswith(self.path + "/")
            and path.endswith("/body.txt")
            and path[len(self.path) + 1 : -len("/body.txt")].isdigit()
        )
        if (
            self.calls >= 2
            or request.method != "GET"
            or request.url.scheme != "https"
            or request.url.host != "mailtrap.io"
            or not allowed
        ):
            raise ToolError("Live probe exceeded its two-GET Mailtrap-only boundary.")
        self.calls += 1
        if self.inner is None:
            self.inner = httpx.HTTPTransport(retries=0)
        return self.inner.handle_request(request)

    def close(self):
        if self.inner is not None:
            self.inner.close()
            self.inner = None


def test_live_controlled_mailtrap_registration_persists(monkeypatch):
    if os.getenv("RUN_MAILTRAP_LIVE") != "true":
        pytest.skip(
            "Opt in with RUN_MAILTRAP_LIVE=true; requires real Mailtrap and DB."
        )
    load_dotenv(ROOT / ".env", override=False)
    monkeypatch.setenv("GEMINI_ENABLED", "false")
    if (os.getenv("MAILTRAP_ACCOUNT_ID"), os.getenv("MAILTRAP_INBOX_ID")) != (
        "2853336",
        "4953522",
    ):
        pytest.fail(
            "Configured IDs do not match the controlled sandbox.", pytrace=False
        )
    transport = BoundedMailtrapTransport(
        os.getenv("MAILTRAP_ACCOUNT_ID"), os.getenv("MAILTRAP_INBOX_ID")
    )
    try:
        payload = read_email(1, transport=transport)
    except ToolError as exc:
        pytest.fail(str(exc), pytrace=False)
    if not payload["messages"]:
        pytest.skip(
            "Mailtrap connected; inbox empty. Insert the controlled test email."
        )
    message = payload["messages"][0]
    if message["subject"] != SUBJECT:
        pytest.fail(
            "Newest message is not the controlled email; no run was created.",
            pytrace=False,
        )

    def not_requested(limit):
        raise NotConnected("Intentionally not requested in this email-only live probe.")

    run = store.create_run("EVT-101", 1)
    run_id = run["id"]
    print(f"Retained PostgreSQL execution: {run_id}")
    # Reuse the actual bounded HTTPS read; do not fetch twice or substitute a fixture.
    execute(
        run_id,
        "EVT-101",
        1,
        adapters={
            "calendar": not_requested,
            "email": lambda limit: payload,
            "web": not_requested,
        },
    )
    store.step(
        run_id, "export", "skipped", error="CSV export not requested by this probe."
    )
    persisted = store.get_run(run_id)
    assert persisted is not None
    assert persisted["status"] == "partial"  # Calendar/Web were deliberately skipped.
    assert persisted["summary"]["tools"] == {
        "calendar": "skipped",
        "email": "completed",
        "web": "skipped",
    }
    assert len(persisted["results"]) == 1
    result = persisted["results"][0]
    assert result["event_id"] == "EVT-101"
    assert result["email"] == "lindi.mokoena@example.com"
    assert result["full_name"] == "Lindi Mokoena-Test"
    assert result["status"] == "review_required"
    assert set(result["issues"]) == {"name_mismatch", "inactive_participant"}
    assert {match["record_id"] for match in result["matches"]} == {"EVT-101", "P-003"}
    assert result["evidence"][0]["source_record_id"] == message["id"]
    assert result["evidence"][0]["source_reference"] == message["source_reference"]
    assert "MAILTRAP-EVT101-001" in result["evidence"][0]["excerpt"]
    steps = {step["node_id"]: step for step in persisted["steps"]}
    assert steps["email"]["outputs"]["messages_read"] == 1
    for node in [
        "email",
        "extraction",
        "normalization",
        "deduplication",
        "verification",
        "discrepancy",
        "persistence",
    ]:
        assert steps[node]["status"] == "completed"
    assert store.get_run(run_id)["results"] == persisted["results"]
    assert transport.calls == 2
