"""Protected service trigger; n8n delegates all verification to LangGraph."""

import hashlib
import hmac
import json
import os
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from psycopg.rows import dict_row

from app.agents.workflow import execute
from app.api.agents import RunRequest
from app.core.database import connect_db
from app.core.demo import consume_budget
from app.services import agent_repository as store

router = APIRouter(prefix="/api/integrations/n8n", tags=["Protected n8n service"])


class Delivery(RunRequest):
    idempotency_key: UUID


def require_service(request: Request):
    expected = os.getenv("N8N_SERVICE_TOKEN", "")
    supplied = request.headers.get("X-EventOps-Service-Key", "")
    if len(expected) < 32:
        raise HTTPException(503, "n8n service integration is not configured.")
    if len(supplied) > 256 or not hmac.compare_digest(supplied.encode(), expected.encode()):
        raise HTTPException(401, "A valid service credential is required.")


@router.post("/runs", status_code=202)
def start(payload: Delivery, tasks: BackgroundTasks):
    if payload.event_id not in {r["record_id"] for r in store.reference_records() if r["record_type"] == "event"}:
        raise HTTPException(422, "Choose an event that exists in the indexed reference data.")
    fingerprint = hashlib.sha256(json.dumps({"event_id": payload.event_id, "max_records": payload.max_records}, sort_keys=True).encode()).hexdigest()
    with connect_db() as connection, connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", ("n8n:" + str(payload.idempotency_key),))
        cursor.execute("SELECT * FROM n8n_deliveries WHERE idempotency_key=%s", (payload.idempotency_key,))
        delivery = cursor.fetchone()
        reused = delivery is not None
        if reused:
            if delivery["payload_hash"] != fingerprint:
                raise HTTPException(409, "This delivery key was already used with different inputs.")
            cursor.execute("SELECT * FROM agent_runs WHERE id=%s", (delivery["run_id"],))
            run = cursor.fetchone()
        else:
            consume_budget("n8n_runs", int(os.getenv("N8N_DAILY_RUN_LIMIT", "10")))
            consume_budget("agent_runs", int(os.getenv("AGENT_DAILY_RUN_LIMIT", "30")))
            try:
                run = store.insert_run(cursor, payload.event_id, payload.max_records)
            except RuntimeError as exc:
                raise HTTPException(409, str(exc)) from exc
            cursor.execute("INSERT INTO n8n_deliveries (idempotency_key,payload_hash,run_id) VALUES (%s,%s,%s)", (payload.idempotency_key, fingerprint, run["id"]))
    if not reused:
        tasks.add_task(execute, run["id"], payload.event_id, payload.max_records)
    return {"id": run["id"], "status": run["status"], "event_id": run["event_id"], "reused": reused, "origin": "service_trigger"}


@router.get("/runs/{run_id}")
def detail(run_id: UUID):
    with connect_db() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM n8n_deliveries WHERE run_id=%s", (run_id,))
        if cursor.fetchone() is None:
            raise HTTPException(404, "Service execution not found.")
    run = store.get_run(run_id)
    if run is None:
        raise HTTPException(404, "Service execution not found.")
    return run
