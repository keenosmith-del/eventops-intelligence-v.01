"""Keep developer dotenv files out of production processes."""

import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
from psycopg.conninfo import conninfo_to_dict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def load_local_environment():
    if os.getenv("APP_ENV") != "production":
        load_dotenv(PROJECT_ROOT / ".env", override=False)


def validate_production_environment():
    if os.getenv("APP_ENV") != "production":
        return
    if os.getenv("DEMO_MODE", "false").lower() != "true":
        raise RuntimeError("Production assessment access requires DEMO_MODE=true.")
    try:
        config = conninfo_to_dict(os.environ["DATABASE_URL"])
        mode = os.getenv("POSTGRES_SSLMODE") or config.get("sslmode")
        if mode not in {"require", "verify-ca", "verify-full"}:
            raise ValueError
        host = config.get("host", "")
        if not host or host in {"localhost", "127.0.0.1", "::1"} or host.startswith("/"):
            raise ValueError
    except Exception:
        raise RuntimeError("Production requires a hosted DATABASE_URL with TLS.") from None
    origins = os.getenv("FRONTEND_ORIGINS", "").split(",")
    for origin in origins:
        parts = urlsplit(origin.strip())
        if (parts.scheme != "https" or not parts.hostname or parts.username
                or parts.password or parts.path not in {"", "/"}
                or parts.query or parts.fragment or "*" in origin):
            raise RuntimeError("Production requires explicit HTTPS FRONTEND_ORIGINS.")


if __name__ == "__main__":
    validate_production_environment()
