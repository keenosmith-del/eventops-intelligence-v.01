import os

import psycopg
from app.core.environment import load_local_environment, validate_production_environment


def connect_db() -> psycopg.Connection:
    """Create a PostgreSQL connection using environment configuration."""

    load_local_environment()
    validate_production_environment()

    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return psycopg.connect(
            database_url,
            connect_timeout=5,
            **({"sslmode": os.environ["POSTGRES_SSLMODE"]} if os.getenv("POSTGRES_SSLMODE") else {}),
        )

    required = [
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
    ]

    missing = [name for name in required if not os.getenv(name)]

    if missing:
        raise RuntimeError("Missing database configuration: " + ", ".join(missing))

    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("POSTGRES_PORT", "55432")),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=5,
        sslmode=os.getenv("POSTGRES_SSLMODE", "prefer"),
    )
