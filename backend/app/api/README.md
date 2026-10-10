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

## Persistent RAG Conversations

Module: conversations.py

The Conversation API connects PostgreSQL conversation
persistence to our existing semantic retrieval system.

### Endpoints

POST /api/conversations
Creates a new conversation.

GET /api/conversations
Lists recent conversations.

GET /api/conversations/{conversation_id}
Retrieves a conversation and its stored messages.

POST /api/conversations/{conversation_id}/messages
Runs retrieval and persists the question and evidence.

### Conversation Flow

1. Validate the conversation identifier.
2. Interpret the submitted question.
3. Generate a local query embedding.
4. Retrieve matching evidence through PostgreSQL.
5. Persist the user question.
6. Persist the retrieval message with evidence.
7. Return the stored exchange.

### Transaction Handling

Question and retrieval messages are written inside
the same PostgreSQL transaction.

Failed database transactions roll back the exchange.

### Evidence Preservation

Stored retrieval messages contain:

- Query plan
- Document identifiers
- Source record identifiers
- Source references
- Similarity scores
- Retrieved content

These are evidence snapshots, not generated answers.

### Current Limitations

- Follow-up questions are not yet context-aware.
- Gemini generation is not yet integrated.
- Conversation ownership is not yet enforced.
- No demonstration session authentication yet.
- No production rate limiting.
- No streaming responses.

These endpoints are for local development only.

They must not be exposed publicly before implementing
backend-validated sessions and conversation access
controls.

### Testing

python -m pytest tests/test_conversation_api.py -v

## Conversation Recovery Verification

The Conversation API supports committed conversation
persistence across application restarts.

Recovery testing covers:

- Creating a conversation over HTTP
- Submitting a question through the RAG pipeline
- Persisting user and retrieval messages
- Preserving source evidence and query plans
- Recreating the PostgreSQL container
- Restarting FastAPI
- Retrieving the original conversation by UUID

This verifies local persistence using PostgreSQL's
named Docker volume.

Conversation access controls and demonstration
session authentication are still required before
public deployment.

## Context-Aware Conversation Retrieval

The conversation message endpoint supports deterministic
context resolution using previously persisted messages.

### Processing Flow

1. Validate the conversation identifier.
2. Load ordered conversation history from PostgreSQL.
3. Resolve clear contextual event references.
4. Interpret the resolved question.
5. Execute PostgreSQL-backed semantic retrieval.
6. Persist the original question and retrieval result.
7. Preserve the context-resolution decision.

### Context Metadata

Retrieval message query plans contain:

context_resolution:
  used_context
  inherited_event_id

The query plan also retains the resolved retrieval query.

The original user question is stored separately and
is not replaced by the enriched retrieval query.

### Error Handling

If a question requires unavailable or ambiguous
context, the endpoint returns HTTP 422.

Such failures do not persist partial exchanges.

Explicitly provided event IDs take precedence over
previous conversation context.

### Limitations

Context resolution currently supports selected
event references only.

It does not provide general conversational reasoning
or multi-entity coreference.

Context is read before the retrieval operation.
Concurrent requests to the same conversation are
not yet serialized across context resolution and
retrieval; this requires further coordination.

Conversation access controls are still required
before public deployment.
