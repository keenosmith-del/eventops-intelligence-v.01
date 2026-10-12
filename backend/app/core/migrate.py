"""Apply numbered migrations once, transactionally; run before serving traffic."""

from pathlib import Path

from app.core.database import connect_db


# Apply all numbered migrations in the infrastructure/postgres/migrations directory that have not yet been applied, in order.
def migrate():
    root = Path(__file__).resolve().parents[3] / "infrastructure/postgres/migrations"
    with connect_db() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(3902102)")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
        )
        for migration in sorted(root.glob("[0-9]*.sql")):
            cursor.execute(
                "SELECT 1 FROM schema_migrations WHERE name=%s", (migration.name,)
            )
            if not cursor.fetchone():
                cursor.execute(migration.read_text())
                cursor.execute(
                    "INSERT INTO schema_migrations (name) VALUES (%s)",
                    (migration.name,),
                )
                print("Applied", migration.name)


if __name__ == "__main__":
    migrate()
