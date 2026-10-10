# Database Migrations

## Purpose

Version-controlled PostgreSQL schema changes for
EventOps Intelligence.

## Migration 001 — Knowledge Records

File: 001_knowledge_records.sql

Creates the knowledge_records table.

The schema supports:

- Persistent structured knowledge records
- Source provenance
- Record-level change detection
- JSONB metadata
- 384-dimensional vector embeddings
- Unique source-record identities
- Event and record-type filtering

## Applying the Migration

From the repository root:

```bash
docker compose exec -T db psql \
  -U eventops \
  -d eventops \
  -X \
  -v ON_ERROR_STOP=1 \
  --single-transaction \
  < infrastructure/postgres/migrations/001_knowledge_records.sql
```

## Migration Strategy

SQL migration files are numbered sequentially.

Applied migrations should not be modified.

Future changes should be introduced through
additional numbered migration files.

The current migration is applied manually.

An automated migration runner and migration-history
tracking will be implemented before production deployment.

## Current Status

Migration 001 defines persistent knowledge storage.

Python database access and record upserts will be
implemented next.

Additional migrations will support:

- RAG conversations
- Chat messages
- Agent execution history
- Tool execution records
- Verification outcomes
- Evidence references
  EOF
