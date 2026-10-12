from uuid import UUID

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.core.database import connect_db

NODES = [
    "trigger",
    "calendar",
    "email",
    "web",
    "extraction",
    "normalization",
    "deduplication",
    "verification",
    "discrepancy",
    "persistence",
    "export",
]


def insert_run(cursor, event_id, max_records, owner=None):
    """Shared transactional admission for reviewer and service triggers."""
    cursor.execute("SELECT pg_advisory_xact_lock(3902101)")
    cursor.execute(
        "SELECT COUNT(*) AS count FROM agent_runs WHERE status IN ('pending','running') AND created_at > NOW() - INTERVAL '10 minutes'"
    )
    if cursor.fetchone()["count"] >= 2:
        raise RuntimeError(
            "Two verification runs are already active. Wait for a run to finish."
        )
    cursor.execute(
        "INSERT INTO agent_runs (event_id,max_records) VALUES (%s,%s) RETURNING *",
        (event_id, max_records),
    )
    row = cursor.fetchone()
    for index, node in enumerate(NODES):
        cursor.execute(
            "INSERT INTO agent_steps (run_id,node_id,position) VALUES (%s,%s,%s)",
            (row["id"], node, index),
        )
    if owner:
        cursor.execute(
            "INSERT INTO demo_objects (object_id,session_id,kind) VALUES (%s,%s,'run')",
            (row["id"], owner),
        )
    return row


def create_run(event_id: str, max_records: int, owner: UUID | None = None) -> dict:
    with connect_db() as connection, connection.cursor(row_factory=dict_row) as cursor:
        return insert_run(cursor, event_id, max_records, owner)


def expire_stale():
    with connect_db() as connection, connection.cursor() as cursor:
        cursor.execute(
            "UPDATE agent_runs SET status='failed', finished_at=NOW(), error='Execution interrupted or exceeded the 10-minute recovery window. Start a new run.' WHERE status IN ('pending','running') AND created_at < NOW() - INTERVAL '10 minutes' RETURNING id"
        )
        for (run_id,) in cursor.fetchall():
            cursor.execute(
                "UPDATE agent_steps SET status='failed', finished_at=NOW(), error='Execution interrupted.' WHERE run_id=%s AND status IN ('pending','running')",
                (run_id,),
            )


def get_run(run_id: UUID, owner: UUID | None = None) -> dict | None:
    expire_stale()
    with connect_db() as connection, connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            "SELECT * FROM agent_runs WHERE id=%s AND (%s::uuid IS NULL OR EXISTS (SELECT 1 FROM demo_objects WHERE object_id=agent_runs.id AND session_id=%s))",
            (run_id, owner, owner),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        cursor.execute(
            "SELECT * FROM agent_steps WHERE run_id=%s ORDER BY position", (run_id,)
        )
        row["steps"] = cursor.fetchall()
    return row


def list_runs(owner: UUID | None = None) -> list[dict]:
    expire_stale()
    with connect_db() as connection, connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            "SELECT id,event_id,status,created_at,finished_at,error,summary FROM agent_runs WHERE (%s::uuid IS NULL OR EXISTS (SELECT 1 FROM demo_objects WHERE object_id=agent_runs.id AND session_id=%s)) ORDER BY created_at DESC LIMIT 30",
            (owner, owner),
        )
        return cursor.fetchall()


def step(run_id, node, status, *, inputs=None, outputs=None, error=None):
    with connect_db() as connection, connection.cursor() as cursor:
        cursor.execute(
            """UPDATE agent_steps SET status=%s,
            started_at=CASE WHEN %s='running' THEN NOW() ELSE started_at END,
            finished_at=CASE WHEN %s IN ('completed','failed','skipped') THEN NOW() ELSE NULL END,
            inputs=COALESCE(%s,inputs), outputs=COALESCE(%s,outputs), error=%s
            WHERE run_id=%s AND node_id=%s""",
            (
                status,
                status,
                status,
                Jsonb(inputs) if inputs is not None else None,
                Jsonb(outputs) if outputs is not None else None,
                error,
                run_id,
                node,
            ),
        )


def set_run(
    run_id, status, *, results=None, summary=None, error=None, persistence_outputs=None
):
    with connect_db() as connection, connection.cursor() as cursor:
        cursor.execute(
            """UPDATE agent_runs SET status=%s, results=COALESCE(%s,results), summary=COALESCE(%s,summary), error=%s,
            finished_at=CASE WHEN %s IN ('completed','partial','failed') THEN NOW() ELSE NULL END WHERE id=%s""",
            (
                status,
                Jsonb(results) if results is not None else None,
                Jsonb(summary) if summary is not None else None,
                error,
                status,
                run_id,
            ),
        )
        if persistence_outputs is not None:
            cursor.execute(
                "UPDATE agent_steps SET status='completed', finished_at=NOW(), outputs=%s WHERE run_id=%s AND node_id='persistence'",
                (Jsonb(persistence_outputs), run_id),
            )


def reference_records() -> list[dict]:
    with connect_db() as connection, connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(
            "SELECT record_id, record_type, event_id, content, metadata FROM knowledge_records ORDER BY record_id"
        )
        return cursor.fetchall()
