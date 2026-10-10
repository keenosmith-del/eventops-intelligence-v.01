# PostgreSQL Infrastructure

## Purpose

Local persistent storage for EventOps Intelligence.

The database will store knowledge records, embeddings,
conversation history, agent execution records and
verification results.

## Technology

- PostgreSQL 17
- pgvector
- Docker Compose
- Docker-managed persistent volume

## Local Configuration

Service: db
Host: 127.0.0.1
Port: 55432
Database: eventops
Username: eventops

Credentials are supplied by the root .env file.

## Start Database

From the repository root:

docker compose up -d db

## Inspect Database

docker compose ps

docker compose logs db

## Stop Database

docker compose stop db

## Persistence

Database files are stored in the named Docker volume
postgres_data.

Stopping or recreating the database container does
not remove the persistent volume.

Do not use docker compose down -v unless intentionally
deleting the database.

## pgvector

The image includes the pgvector extension files.

The extension must be enabled inside the application
database using CREATE EXTENSION.

Vector indexing and application schema migrations
will be implemented in subsequent milestones.

## Security

- Local-only database port binding
- Database credentials excluded from Git
- No public database exposure
- No external database service required

## Current Status

Container configuration is implemented.

Database availability, extension activation and
persistence must be verified before this milestone
is considered complete.

## Operating Cost

Runs locally through Docker Desktop.

No cloud database subscription or paid API required.

## Verified Persistence and Recovery

The knowledge repository was tested with:

- 19 structured knowledge records
- 19 persistent 384-dimensional embeddings
- PostgreSQL-backed source metadata
- Idempotent repeated indexing
- PostgreSQL integration tests

Container recreation can be tested using:

docker compose up -d --force-recreate --wait db

The named Docker volume preserves database contents
across container replacement.

After recreation, verify:

SELECT
    COUNT(*) AS total_records,
    COUNT(embedding) AS stored_embeddings
FROM knowledge_records;

Expected values for the current reference dataset:

- 19 knowledge records
- 19 stored embeddings

Repeat the indexing operation:

python -m app.rag.indexing

Unchanged records should not be rewritten or embedded
again.

Important:

Never use docker compose down -v unless intentionally
deleting the database.

This test verifies local persistence only.

Cloud database recovery, backup restoration and
multi-instance concurrency remain unverified.
