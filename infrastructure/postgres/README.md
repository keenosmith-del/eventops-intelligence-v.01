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
