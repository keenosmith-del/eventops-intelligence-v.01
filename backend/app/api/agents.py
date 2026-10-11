import csv
import io
import re
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import Response
from pydantic import Field

from app.agents.workflow import execute
from app.core.demo import consume_budget, session_id
from app.integrations.tools import connection_info
from app.models.domain import DomainModel
from app.services import agent_repository as repository

router = APIRouter(prefix="/api/agents", tags=["Verification agent"])


class RunRequest(DomainModel):
    event_id: str = Field(default="EVT-101", pattern=r"^EVT-\d{3}$")
    max_records: int = Field(default=20, ge=1, le=30)


@router.get("/connections")
def connections():
    return connection_info()


@router.post("/runs", status_code=202)
def start_run(payload: RunRequest, request: Request, tasks: BackgroundTasks):
    if payload.event_id not in {
        r["record_id"]
        for r in repository.reference_records()
        if r["record_type"] == "event"
    }:
        raise HTTPException(
            422, "Choose an event that exists in the indexed reference data."
        )
    consume_budget(
        "agent_runs", int(__import__("os").getenv("AGENT_DAILY_RUN_LIMIT", "30"))
    )
    try:
        run = repository.create_run(
            payload.event_id, payload.max_records, session_id(request)
        )
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from exc
    tasks.add_task(execute, run["id"], payload.event_id, payload.max_records)
    return run


@router.get("/runs")
def runs(request: Request):
    return repository.list_runs(session_id(request))


def require_run(run_id, request):
    run = repository.get_run(run_id, session_id(request))
    if run is None:
        raise HTTPException(404, "Execution not found in this demonstration session.")
    return run


@router.get("/runs/{run_id}")
def detail(run_id: UUID, request: Request):
    return require_run(run_id, request)


@router.get("/runs/{run_id}/results")
def results(run_id: UUID, request: Request):
    run = require_run(run_id, request)
    return {
        "run_id": run_id,
        "status": run["status"],
        "summary": run["summary"],
        "records": run["results"],
    }


def csv_safe(value):
    value = str("" if value is None else value)
    return "'" + value if re.match(r"^\s*[=+@\-]", value) else value


@router.get("/runs/{run_id}/export.csv")
def export(run_id: UUID, request: Request, verified_only: bool = False):
    run = require_run(run_id, request)
    if run["status"] in ("pending", "running"):
        raise HTTPException(409, "Wait for the execution to finish before exporting.")
    fields = [
        "id",
        "status",
        "event_id",
        "title",
        "full_name",
        "email",
        "starts_at",
        "venue",
        "duplicate_count",
        "issues",
        "source_references",
        "reference_matches",
    ]
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=fields)
    writer.writeheader()
    for item in run["results"]:
        if verified_only and item["status"] != "verified":
            continue
        row = {key: item.get(key, "") for key in fields}
        row["issues"] = "; ".join(item["issues"])
        row["source_references"] = "; ".join(
            e["source_reference"] for e in item["evidence"]
        )
        row["reference_matches"] = "; ".join(m["record_id"] for m in item["matches"])
        writer.writerow({k: csv_safe(v) for k, v in row.items()})
    # Downloads must not mutate the recorded execution or its replay clock.
    return Response(
        "\ufeff" + out.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="eventops-{run_id}.csv"',
            "Cache-Control": "no-store",
        },
    )
