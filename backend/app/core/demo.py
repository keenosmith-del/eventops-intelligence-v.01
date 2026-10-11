"""Anonymous demonstration sessions: isolation and budgets, not user authentication."""

import hashlib
import os
import secrets
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from psycopg.rows import dict_row

from app.core.database import connect_db

router = APIRouter(prefix="/api/demo", tags=["Reviewer demo"])


def demo_enabled() -> bool:
    return os.getenv("DEMO_MODE", "false").lower() == "true"


def session_id(request: Request) -> UUID | None:
    return getattr(request.state, "demo_session_id", None)


def consume_budget_in_transaction(cursor, bucket: str, limit: int) -> None:
    if limit < 1:
        raise HTTPException(429, "This demonstration operation is disabled by its server-side budget.")
    cursor.execute(
        """INSERT INTO demo_usage (bucket, requests) VALUES (%s, 1)
        ON CONFLICT (bucket, day) DO UPDATE SET requests = demo_usage.requests + 1
        WHERE demo_usage.requests < %s RETURNING requests""",
        (bucket, limit),
    )
    if cursor.fetchone() is None:
        raise HTTPException(429, "The demonstration request budget has been reached. Try again tomorrow.")


def consume_budget(bucket: str, limit: int) -> None:
    with connect_db() as connection, connection.cursor() as cursor:
        consume_budget_in_transaction(cursor, bucket, limit)


@router.post("/session")
def create_demo_session():
    # Durable global cap prevents anonymous session creation bypassing quotas.
    token = secrets.token_urlsafe(32)
    with connect_db() as connection, connection.cursor(row_factory=dict_row) as cursor:
        # Admission and insertion share one connection/transaction. Failed entry
        # must not consume the durable session allowance.
        consume_budget_in_transaction(cursor, "sessions", int(os.getenv("DEMO_SESSION_LIMIT", "100")))
        cursor.execute(
            "INSERT INTO demo_sessions (token_hash) VALUES (%s) RETURNING expires_at",
            (hashlib.sha256(token.encode()).hexdigest(),),
        )
        expires = cursor.fetchone()["expires_at"]
    return {
        "session_token": token,
        "expires_at": expires,
        "demo_mode": demo_enabled(),
        "notice": "Reviewer demonstration access. This is not account authentication. Use synthetic data only.",
    }


def identify_session(token: str | None) -> UUID:
    if not token or len(token) > 128:
        raise HTTPException(
            401, "Continue as reviewer to start a demonstration session."
        )
    with connect_db() as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT id FROM demo_sessions WHERE token_hash = %s AND expires_at > NOW()",
            (hashlib.sha256(token.encode()).hexdigest(),),
        )
        row = cursor.fetchone()
    if row is None:
        raise HTTPException(
            401, "Your demonstration session expired. Continue as reviewer again."
        )
    return row[0]


@router.get("/config")
def demo_config():
    return {
        "demo_mode": demo_enabled(),
        "generation_enabled": os.getenv("GEMINI_ENABLED") == "true",
        "email_mode": "sandbox_read_only",
        "authentication": "demonstration_only",
    }
