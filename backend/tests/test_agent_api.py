import csv
import io
from uuid import uuid4

import pytest
from app.agents.workflow import execute
from app.api.agents import csv_safe
from app.core.database import connect_db
from app.core.demo import consume_budget
from app.integrations import tools
from app.main import app
from app.services import agent_repository as store
from fastapi.testclient import TestClient


@pytest.fixture
def run():
    row = store.create_run("EVT-101", 10)
    yield row
    with connect_db() as connection, connection.cursor() as cursor:
        cursor.execute("DELETE FROM agent_runs WHERE id=%s", (row["id"],))


def fake_adapters():
    def calendar(limit):
        return {
            "source_reference": "https://example.com/calendar.ics",
            "body": "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n",
        }

    def email(limit):
        raise tools.NotConnected("Test-only missing configuration")

    def web(limit):
        return {
            "source_reference": "https://example.com/registrations",
            "body": '[{"event_id":"EVT-101","full_name":"Ada Mensah","email":"ada.mensah@example.com"}]',
        }

    return {"calendar": calendar, "email": email, "web": web}


def test_graph_persists_real_step_outcomes_with_explicit_test_adapters(run):
    execute(run["id"], "EVT-101", 10, adapters=fake_adapters())
    restored = store.get_run(run["id"])
    assert restored["status"] == "partial"
    assert restored["summary"]["verified"] == 1
    steps = {s["node_id"]: s for s in restored["steps"]}
    assert steps["email"]["status"] == "skipped"
    assert steps["verification"]["status"] == "completed"
    assert steps["export"]["status"] == "pending"
    response = TestClient(app).get(f"/api/agents/runs/{run['id']}/export.csv")
    assert response.status_code == 200
    exported = list(csv.DictReader(io.StringIO(response.text.lstrip("\ufeff"))))
    assert exported[0]["email"] == "ada.mensah@example.com"
    after_export = store.get_run(run["id"])
    assert after_export["steps"] == restored["steps"]
    assert after_export["finished_at"] == restored["finished_at"]


def test_failing_tool_is_reported_not_fabricated(run):
    adapters = fake_adapters()

    def failed(limit):
        raise tools.ToolError("Test-only provider outage")

    adapters["web"] = failed
    execute(run["id"], "EVT-101", 10, adapters=adapters)
    restored = store.get_run(run["id"])
    assert restored["status"] == "partial"
    assert restored["summary"]["tools"]["web"] == "failed"
    assert restored["results"] == []


def test_results_and_export_scoped_to_demo_session(run, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    client = TestClient(app)
    token = client.post("/api/demo/session").json()["session_token"]
    headers = {"X-Demo-Session": token}
    assert client.get("/api/conversations").status_code == 401
    assert (
        client.get(f"/api/agents/runs/{run['id']}", headers=headers).status_code == 404
    )
    first = client.post(
        "/api/conversations", json={"title": "Isolated reviewer"}, headers=headers
    )
    assert first.status_code == 201
    cid = first.json()["id"]
    other = client.post("/api/demo/session").json()["session_token"]
    assert (
        client.get(
            f"/api/conversations/{cid}", headers={"X-Demo-Session": other}
        ).status_code
        == 404
    )
    assert not any(
        x["id"] == cid
        for x in client.get(
            "/api/conversations", headers={"X-Demo-Session": other}
        ).json()
    )
    assert client.get(f"/api/conversations/{cid}", headers=headers).status_code == 200
    with connect_db() as connection, connection.cursor() as cursor:
        cursor.execute("DELETE FROM rag_conversations WHERE id=%s", (cid,))
        cursor.execute("DELETE FROM demo_objects WHERE object_id=%s", (cid,))


def test_invalid_event_and_bounded_inputs():
    client = TestClient(app)
    assert (
        client.post(
            "/api/agents/runs", json={"event_id": "EVT-999", "max_records": 5}
        ).status_code
        == 422
    )
    assert client.post("/api/agents/runs", json={"max_records": 31}).status_code == 422
    assert (
        client.post(
            "/api/agents/runs", json={"url": "https://malicious.example"}
        ).status_code
        == 422
    )


def test_csv_formula_injection_is_neutralized():
    for value in ["=SUM(A1:A2)", "+123", "@evil", " -danger"]:
        assert csv_safe(value).startswith("'")
    assert csv_safe("normal") == "normal"
    assert csv_safe(0) == "0"


def test_durable_budget_cannot_be_bypassed():
    bucket = "test:" + str(uuid4())
    consume_budget(bucket, 1)
    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        consume_budget(bucket, 1)
    with pytest.raises(HTTPException):
        consume_budget(bucket + "zero", 0)
    with connect_db() as connection, connection.cursor() as cursor:
        cursor.execute("DELETE FROM demo_usage WHERE bucket=%s", (bucket,))


def test_generation_budget_covers_pydantic_boolean_coercion(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("GEMINI_DAILY_LIMIT", "0")
    client = TestClient(app)
    token = client.post("/api/demo/session", json={}).json()["session_token"]
    for value in [True, "true", "yes", 1]:
        response = client.post(
            f"/api/conversations/{uuid4()}/messages",
            json={"question": "EVT-101", "generate_answer": value},
            headers={"X-Demo-Session": token},
        )
        assert response.status_code == 429


def test_prepared_mailtrap_cases_use_authoritative_identities(run):
    """Offline regression for prepared payloads, not a live-provider claim."""
    import json
    from pathlib import Path
    payloads = json.loads((Path(__file__).resolve().parents[2] / "docs/testing/mailtrap/final-assessment.json").read_text())
    adapters = fake_adapters()
    adapters["web"] = lambda limit: {"source_reference": "https://example.com/explicit-offline-test", "body": "[]"}
    adapters["email"] = lambda limit: {"source_reference": "explicit-offline-test", "messages": [{"id": str(i), "subject": p["subject"], "body": p["text"], "source_reference": f"explicit-offline-test/{i}"} for i, p in enumerate(payloads)]}
    execute(run["id"], "EVT-101", 5, adapters=adapters)
    restored = store.get_run(run["id"])
    assert restored["summary"]["verified"] == 1
    assert restored["summary"]["flagged"] == 1
    assert restored["summary"]["duplicates_merged"] == 1
    ada = next(r for r in restored["results"] if r["email"] == "ada.mensah@example.com")
    assert ada["status"] == "verified" and ada["duplicate_count"] == 1
    assert {m["record_id"] for m in ada["matches"]} == {"EVT-101", "P-001"}
    inactive = next(r for r in restored["results"] if r["email"] == "lindi.mokoena@example.com")
    assert {"inactive_participant", "name_mismatch"}.issubset(inactive["issues"])


def test_failed_session_insert_rolls_back_session_budget(monkeypatch):
    from app.core import demo
    token = "explicit-test-only-" + str(uuid4())
    monkeypatch.setattr(demo.secrets, "token_urlsafe", lambda size: token)
    monkeypatch.setenv("DEMO_SESSION_LIMIT", "10000")
    client = TestClient(app)
    first = client.post("/api/demo/session")
    assert first.status_code == 200
    with connect_db() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT requests FROM demo_usage WHERE bucket='sessions' AND day=CURRENT_DATE")
        admitted = cursor.fetchone()[0]
    assert client.post("/api/demo/session").status_code == 503
    with connect_db() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT requests FROM demo_usage WHERE bucket='sessions' AND day=CURRENT_DATE")
        assert cursor.fetchone()[0] == admitted
        import hashlib
        cursor.execute("DELETE FROM demo_sessions WHERE token_hash=%s", (hashlib.sha256(token.encode()).hexdigest(),))
