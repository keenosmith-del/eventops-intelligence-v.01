# RAG — Retrieval-Augmented Generation

## Purpose

This module implements structured knowledge ingestion
and will progressively introduce semantic retrieval,
embeddings and grounded generation.

The RAG system supports questions about events,
operational policies and participant reference data.

## Current Implementation

Implemented:

- CSV ingestion
- JSON ingestion
- Pydantic schema validation
- Cross-document reference validation
- Duplicate identifier detection
- Structure-aware record chunking
- Source provenance metadata
- Deterministic source fingerprints
- Automated ingestion tests

Not yet implemented:

- Embedding generation
- Vector storage
- Semantic similarity retrieval
- Query transformation
- Gemini answer generation
- Source citation rendering
- Conversation persistence

## Source Documents

Located in data/structured/:

- events.csv
- policies.csv
- directory.json

Current source data contains:

- 3 events
- 9 policies
- 7 participants

Expected ingestion output: 19 KnowledgeRecord objects.

## Ingestion

Entry point:

app/rag/ingestion.py

Function:

ingest_structured_documents(data_dir=None)

Returns:

list[KnowledgeRecord]

The function reads and validates all three documents.

It rejects invalid schemas, duplicate identifiers,
and references to unknown events.

The function performs no network requests.

## Chunking Strategy

Each source record becomes one semantic knowledge
unit instead of using arbitrary character boundaries.

Event chunks contain schedules, venue and capacity.

Policy chunks contain scope, category and rule text.

Participant chunks contain reference identity,
directory status and event associations.

These units preserve business meaning and make
source tracing straightforward.

## Source Provenance

Each knowledge record preserves:

- document_id
- record_id
- event_id where applicable
- source_path
- source_reference
- source_sha256

The source reference uses a stable record identifier.

SHA-256 fingerprints are derived from normalized
structured records.

These fingerprints can later support incremental
indexing and changed-record detection.

## Reproducibility

Repeated ingestion of unchanged documents generates
equivalent knowledge records.

This does not yet establish idempotent database writes.

Persistent indexing will require record upserts
and removal of stale indexed records.

## Testing

From backend/:

python -m pytest tests/test_rag_ingestion.py -v

## Planned Architecture

Structured documents
-> Schema validation
-> KnowledgeRecord chunks
-> Embedding generation
-> Vector indexing
-> Query transformation
-> Semantic retrieval
-> Gemini grounded generation
-> Evidence-backed answer

## Engineering Constraints

- No paid APIs are required for local ingestion.
- No LLM is used to validate authoritative data.
- Source references must survive retrieval.
- Missing evidence must not be fabricated.
- Ingestion errors must be explicit.
- Original structured records remain authoritative.
