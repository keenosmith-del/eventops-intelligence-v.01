# API Layer

## Purpose

HTTP interfaces for EventOps Intelligence.

## Implemented Endpoints

### GET /health

Returns basic application process health.

### POST /api/rag/retrieve

Accepts a natural-language question and returns
ranked source evidence from PostgreSQL.

Request example:

{
"question": "Where is EVT-101 being held?",
"top_k": 5
}

Response includes:

- Original question
- Interpreted query plan
- Evidence count
- Retrieved knowledge records
- Cosine similarity scores
- Original document and record identifiers
- Source references and metadata

## Architecture

FastAPI
-> Query interpretation
-> Local query embedding
-> PostgreSQL pgvector retrieval
-> Typed evidence response

## Dependencies

The retrieval route uses FastAPI dependency injection.

LocalEmbeddingModel is cached per server process.

PostgreSQL connections are created for requests
and closed afterwards.

## Current Limitations

- Returns retrieved evidence, not generated answers
- No persistent conversations yet
- No streaming response
- No production access controls yet
- No API rate limiting yet
- No dedicated database-failure response handling yet

This endpoint is intended for local development.
Do not expose it publicly until access controls
and resource limits have been implemented.

## Testing

From backend/:

python -m pytest tests/test_rag_api.py -v

Run the backend:

python -m uvicorn app.main:app \
 --reload --reload-dir app \
 --host 127.0.0.1 --port 5050
