"""Persisted stages and protected service tests; no live provider calls."""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from uuid import uuid4

import pytest

from fastapi import BackgroundTasks
from fastapi.testclient import TestClient
from app.agents.workflow import execute
from app.core.database import connect_db
from app.main import app
from app.services import agent_repository as store
from app.verification.pipeline import deduplicate, normalize, verify
from test_agent_api import fake_adapters
from test_agent_pipeline import candidate, references


@pytest.fixture(autouse=True)
def isolated_service_budget(monkeypatch):
    # Exercise the real PostgreSQL limiter without spending production run quotas.
    import app.api.n8n as service
    from app.core.demo import consume_budget

    prefix = "part2-test-" + uuid4().hex + "-"
    monkeypatch.setattr(
        service,
        "consume_budget",
        lambda bucket, limit: consume_budget(prefix + bucket, limit),
    )
    yield
    with connect_db() as connection, connection.cursor() as cursor:
        cursor.execute("DELETE FROM demo_usage WHERE bucket LIKE %s", (prefix + "%",))


def remove(run_id):
    with connect_db() as connection, connection.cursor() as cursor:
        cursor.execute("DELETE FROM agent_runs WHERE id=%s", (run_id,))


def test_persisted_progress_and_atomic_completion():
    run = store.create_run("EVT-101", 10)
    entered, release = Event(), Event()
    adapters = fake_adapters()
    original = adapters["calendar"]

    def gated(limit):
        entered.set()
        assert release.wait(5)
        return original(limit)

    adapters["calendar"] = gated
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            worker = pool.submit(execute, run["id"], "EVT-101", 10, adapters=adapters)
            try:
                assert entered.wait(5)
                response = TestClient(app).get(f"/api/agents/runs/{run['id']}")
                assert response.status_code == 200
                snapshot = response.json()
                stages = {step["node_id"]: step for step in snapshot["steps"]}
                assert snapshot["status"] == "running"
                assert stages["trigger"]["status"] == "completed"
                assert stages["calendar"]["status"] == "running"
                assert (
                    stages["calendar"]["started_at"]
                    and not stages["calendar"]["finished_at"]
                )
                assert stages["extraction"]["status"] == "pending"
            finally:
                release.set()
            worker.result(timeout=5)
        finished = store.get_run(run["id"])
        assert finished["status"] == "partial"
        assert (
            next(
                step for step in finished["steps"] if step["node_id"] == "persistence"
            )["status"]
            == "completed"
        )
        assert finished["summary"]["execution_mode"] == "controlled_adapter_test"
        extracted = next(
            step for step in finished["steps"] if step["node_id"] == "extraction"
        )
        assert extracted["outputs"]["source_counts"] == {"calendar": 0, "web": 1}
    finally:
        release.set()
        remove(run["id"])


def test_checks_preserve_reference_and_mismatch_values():
    item = candidate(email="lindi.mokoena@example.com", full_name="Lindi Mokoena-Test")
    result = verify(deduplicate(normalize([item])), references(), "EVT-101")[0]
    assert set(result["issues"]) == {"inactive_participant", "name_mismatch"}
    checks = {check["rule"]: check for check in result["checks"]}
    assert checks["participant_name"] == {
        "rule": "participant_name",
        "field": "full_name",
        "actual": "Lindi Mokoena-Test",
        "reference": "Lindi Mokoena",
        "status": "failed",
    }
    assert checks["active_participant"]["actual"] == "inactive"
    assert checks["event_reference"]["status"] == "passed"
    assert (
        next(match for match in result["matches"] if match["record_id"] == "P-003")[
            "fields"
        ]["status"]
        == "inactive"
    )


def test_n8n_auth_idempotency_and_session_isolation(monkeypatch):
    import app.api.n8n as service

    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("N8N_SERVICE_TOKEN", "test-only-service-key-" + uuid4().hex)
    headers = {"X-EventOps-Service-Key": os.environ["N8N_SERVICE_TOKEN"]}
    calls = []

    def controlled(run_id, event_id, limit):
        calls.append(run_id)
        execute(run_id, event_id, limit, adapters=fake_adapters())

    monkeypatch.setattr(service, "execute", controlled)
    client = TestClient(app)
    path = "/api/integrations/n8n/runs"
    payload = {
        "idempotency_key": str(uuid4()),
        "event_id": "EVT-101",
        "max_records": 10,
    }
    assert client.post(path, json=payload).status_code == 401
    token = client.post("/api/demo/session").json()["session_token"]
    reviewer = {"X-Demo-Session": token}
    assert client.post(path, headers=reviewer, json=payload).status_code == 401
    response = client.post(path, headers=headers, json=payload)
    assert response.status_code == 202
    run_id = response.json()["id"]
    try:
        again = client.post(path, headers=headers, json=payload)
        assert again.status_code == 202 and again.json()["reused"] is True
        assert again.json()["id"] == run_id and len(calls) == 1
        assert (
            client.post(
                path, headers=headers, json=payload | {"max_records": 5}
            ).status_code
            == 409
        )
        assert (
            client.get(path + "/" + run_id, headers=headers).json()["status"]
            == "partial"
        )
        assert client.get(path + "/" + run_id, headers=reviewer).status_code == 401
        assert (
            client.get("/api/agents/runs/" + run_id, headers=reviewer).status_code
            == 404
        )
        assert client.get(path + "/" + str(uuid4()), headers=headers).status_code == 404
        assert (
            client.post(
                path,
                headers=headers,
                json=payload | {"url": "https://untrusted.example"},
            ).status_code
            == 422
        )
        assert (
            client.post(
                path, headers=headers, json=payload | {"max_records": 31}
            ).status_code
            == 422
        )
    finally:
        remove(run_id)


def test_n8n_disabled_without_configuration(monkeypatch):
    monkeypatch.delenv("N8N_SERVICE_TOKEN", raising=False)
    response = TestClient(app).post("/api/integrations/n8n/runs", json={})
    assert response.status_code == 503


def test_n8n_delivery_race_creates_one_run(monkeypatch):
    from app.api.n8n import Delivery, start

    monkeypatch.setenv("N8N_DAILY_RUN_LIMIT", "100")
    payload = Delivery(idempotency_key=uuid4(), event_id="EVT-101", max_records=1)

    def invoke(_):
        tasks = BackgroundTasks()
        return start(payload, tasks), len(tasks.tasks)

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(invoke, range(2)))
    run_id = responses[0][0]["id"]
    try:
        assert responses[1][0]["id"] == run_id
        assert sorted(tasks for _, tasks in responses) == [0, 1]
        assert sorted(response["reused"] for response, _ in responses) == [False, True]
    finally:
        remove(run_id)


def test_workflow_is_protected_bounded_and_unactivated():
    root = Path(__file__).resolve().parents[2]
    workflow = json.loads(
        (root / "automations/n8n/eventops-verification.json").read_text()
    )
    nodes = {node["name"]: node for node in workflow["nodes"]}
    assert workflow["active"] is False
    assert nodes["Protected trigger"]["parameters"]["authentication"] == "headerAuth"
    assert (
        nodes["Start verification"]["parameters"]["genericAuthType"] == "httpHeaderAuth"
    )
    assert "$runIndex >= 29" in nodes["Bound polling"]["parameters"]["jsCode"]
    assert not workflow.get("pinData")
    assert (
        workflow["connections"]["Execution finished"]["main"][1][0]["node"]
        == "Wait before status"
    )


def controlled_sources():
    """Synthetic assessment inputs, never used by runtime adapters."""
    calendar = {
        "source_reference": "https://example.com/controlled-assessment.ics",
        "body": "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:assessment-event\r\nSUMMARY:AI Engineering Summit\r\nDESCRIPTION:EVT-101\r\nDTSTART:20261021T070000Z\r\nLOCATION:Cape Town Convention Centre\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n",
    }
    messages = [
        {
            "id": "assessment-ada",
            "subject": "Controlled registration EVT-101",
            "body": "Name: Ada   Mensah\nEmail: ADA.MENSAH@EXAMPLE.COM",
        },
        {
            "id": "assessment-lindi",
            "subject": "Controlled registration EVT-101",
            "body": "Name: Lindi Mokoena-Test\nEmail: lindi.mokoena@example.com",
        },
        {
            "id": "assessment-missing",
            "subject": "Controlled missing event",
            "body": "Name: Unknown Person\nEmail: unknown@example.com",
        },
    ]
    for message in messages:
        message["source_reference"] = (
            "https://example.com/controlled-mail/" + message["id"]
        )
    web = {
        "source_reference": "https://example.com/controlled-registrations",
        "body": json.dumps(
            [
                {
                    "event_id": "EVT-101",
                    "email": "ada.mensah@example.com",
                    "full_name": "Ada Mensah",
                    "title": "Duplicate controlled registration",
                },
                {
                    "event_id": "EVT-101",
                    "email": "unseen@example.com",
                    "full_name": "Unseen Participant",
                    "title": "Unknown controlled participant",
                },
            ]
        ),
    }
    return {
        "calendar": lambda limit: calendar,
        "email": lambda limit: {
            "source_reference": "https://example.com/controlled-mail",
            "messages": messages,
        },
        "web": lambda limit: web,
    }


def test_controlled_assessment_persist_inspect_export_and_restore(monkeypatch):
    import csv
    import io
    from app.core.demo import identify_session

    monkeypatch.setenv("DEMO_MODE", "true")
    client = TestClient(app)
    token = client.post("/api/demo/session").json()["session_token"]
    headers = {"X-Demo-Session": token}
    run = store.create_run("EVT-101", 10, identify_session(token))
    try:
        execute(
            run["id"],
            "EVT-101",
            10,
            adapters=controlled_sources(),
            execution_mode="controlled_assessment_fixture",
        )
        path = f"/api/agents/runs/{run['id']}"
        response = client.get(path, headers=headers)
        assert response.status_code == 200
        saved = response.json()
        assert saved["summary"] == {
            "total": 5,
            "verified": 2,
            "flagged": 3,
            "duplicates_merged": 1,
            "tools": {
                "calendar": "completed",
                "email": "completed",
                "web": "completed",
            },
            "execution_mode": "controlled_assessment_fixture",
        }
        codes = {issue for record in saved["results"] for issue in record["issues"]}
        assert {
            "inactive_participant",
            "name_mismatch",
            "missing_event_id",
            "participant_not_in_directory",
        } <= codes
        assert all(record["checks"] for record in saved["results"])
        for verified_only, count in [(False, 5), (True, 2)]:
            exported = client.get(
                path + "/export.csv",
                params={"verified_only": verified_only},
                headers=headers,
            )
            assert exported.status_code == 200
            rows = list(csv.DictReader(io.StringIO(exported.text.lstrip("\ufeff"))))
            assert len(rows) == count
            assert {row["id"] for row in rows} <= {
                record["id"] for record in saved["results"]
            }
            if verified_only:
                assert all(row["status"] == "verified" for row in rows)
        assert client.get(path, headers=headers).json()["results"] == saved["results"]
        assert any(
            item["id"] == str(run["id"])
            for item in client.get("/api/agents/runs", headers=headers).json()
        )
        if os.getenv("RETAIN_CONTROLLED_ASSESSMENT") == "true":
            print("Retained controlled synthetic assessment execution:", run["id"])
    finally:
        if os.getenv("RETAIN_CONTROLLED_ASSESSMENT") != "true":
            remove(run["id"])
