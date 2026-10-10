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

## Optional Grounded Answer Generation

Endpoint:

POST /api/conversations/{conversation_id}/messages

The request supports:

- question
- top_k
- generate_answer

Generation defaults to false.

### Generation Modes

generate_answer=false:
Retrieves and persists evidence only.

generate_answer=true:
Runs retrieval and requests a grounded answer
from the optional generation service.

Generation remains subject to GEMINI_ENABLED and
GEMINI_API_KEY server configuration.

### Response

The response includes generation_status:

- not_requested
- generated
- insufficient_evidence
- unavailable

Successful generation produces three messages:

1. User question
2. Assistant retrieval evidence
3. Assistant generated answer with citations

When generation is unavailable, the valid retrieval
exchange is still persisted.

### Source Verification

The generation service validates source record IDs.

The conversation repository independently verifies
citation identifiers and source references against
the preceding retrieval message.

Unsupported generated citations are rejected.

Citation matching does not independently prove
claim-level factual correctness.

### Transaction Design

Generation occurs before the exchange is written
to PostgreSQL.

Question, retrieval and optional answer messages
are written using the same database transaction.

A failed generated answer does not require the
retrieval result to be discarded.

The current request dependency may hold a read
transaction during generation.

Concurrent conversation access and transaction
lifetime management require further hardening.

### Testing

python -m pytest tests/test_conversation_api.py -v

Generation is mocked in API tests.

No live provider access is required.

## Verified Generation-Disabled HTTP Workflow

The optional generation endpoint has been tested
with GEMINI_ENABLED=false.

Test request:

POST /api/conversations/{id}/messages

{
  "question": "What time does check-in close for EVT-101?",
  "top_k": 3,
  "generate_answer": true
}

Expected verified behaviour:

- HTTP 200 response
- generation_status=unavailable
- Original user question persisted
- Retrieval message persisted
- POL-003 evidence returned
- Original policy source reference preserved
- No generated-answer message created
- No Gemini provider request

This demonstrates that retrieval and conversation
persistence remain operational when generation is
disabled or unavailable.

Successful live Gemini generation has not yet
been verified.

## Live Generated-Answer Persistence

The complete Conversation API generation workflow
has been verified with real Gemini generation.

A successful request persisted:

1. The original user question
2. The PostgreSQL retrieval result
3. The generated answer and verified citation

The conversation was reloaded through the API,
and all three messages were recovered.

The retrieved source was POL-003, and the generated
answer correctly identified the 08:45 check-in
deadline for EVT-101.

Generation is disabled by default and must not be
enabled for public access without session security,
request limits and usage monitoring.
