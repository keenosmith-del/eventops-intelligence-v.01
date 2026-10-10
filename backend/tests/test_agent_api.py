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
    assert store.get_run(run["id"])["steps"][-1]["status"] == "completed"


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
