# Application Services

## Purpose

Business and persistence services used by EventOps Intelligence.

## Knowledge Repository

Module: knowledge_repository.py

Provides PostgreSQL storage for structured RAG records.

### Implemented operations

- Insert new knowledge records
- Update changed records
- Prevent duplicate source identities
- Retrieve records by source identity
- Count persisted records
- Identify records without embeddings
- Store 384-dimensional vectors
- Invalidate embeddings when source content changes

### Persistence

The repository uses the knowledge_records table
defined in PostgreSQL migration 001.

All database operations use parameterized SQL.

JSONB metadata preserves source references and
structured retrieval attributes.

### Transaction management

The repository receives an existing database connection.

It does not commit transactions independently.

Calling services control transaction boundaries.

### Indexing

The RAG indexing coordinator is located at:

app/rag/indexing.py

Run from backend/:

python -m app.rag.indexing

It validates the source documents, persists knowledge
records and generates embeddings for records that
currently require them.

### Limitations

- Stale records are not yet deleted when removed
  from source documents.
- Concurrent indexing is not yet coordinated.
- Vector similarity queries still need to be moved
  into PostgreSQL.
- Embedding model version metadata is not yet stored.
- Database migrations are not yet automated.

### Testing

PostgreSQL must be running locally.

Run:

python -m pytest tests/test_knowledge_repository.py -v

Integration tests use transaction rollback to
avoid persisting temporary test records.

## Cost

All operations use local PostgreSQL and local
embedding inference. No paid API is required.

## Persistent Indexing Verification

The current structured knowledge base contains:

- 3 event records
- 9 policy records
- 7 participant records

All 19 records support persistent local embeddings.

Repeated ingestion of unchanged source data produces
zero database updates and zero new embeddings.

The knowledge repository supports transaction-based
integration tests and changed-source invalidation.

PostgreSQL uses a persistent Docker volume.

Container recreation and subsequent indexing are used
to verify local recovery.

This is not yet a production backup or disaster
recovery implementation.

## Database Vector Retrieval

The RAG module includes a PostgreSQL-backed semantic
retriever in app/rag/postgres_retrieval.py.

The repository stores knowledge records and embeddings.

The retriever executes cosine similarity ranking
against those persistent embeddings.

This separates write-oriented knowledge persistence
from read-oriented semantic retrieval.

Both components use the shared PostgreSQL connection
infrastructure provided by app/core/database.py.

## Conversation Repository

Module: conversation_repository.py

Persists RAG conversation sessions and messages
using PostgreSQL.

### Implemented Operations

- Create conversations
- Retrieve conversations by UUID
- List recent conversations
- Retrieve ordered message history
- Persist question/retrieval message pairs
- Preserve query plans and source evidence

### Transaction Design

The repository receives an existing PostgreSQL connection.

It does not commit independently.

The caller controls transaction boundaries.

A retrieval exchange writes both the user question
and retrieval result inside one database transaction.

If the transaction rolls back, neither message persists.

### Evidence Persistence

Retrieval messages preserve:
- The interpreted query plan
- Retrieved source records
- Record identifiers
- Source references
- Retrieval scores where supplied

The retrieval summary is not an AI-generated answer.

### Concurrency

The repository locks the conversation row when
appending an exchange.

This coordinates concurrent message writes to the
same conversation.

### Current Limitations

- Conversation history is stored but not yet used
  for follow-up query interpretation.
- No conversation ownership or access-control layer yet.
- No public conversation endpoints yet.
- No response streaming.
- No generated-answer persistence workflow yet.
- No production connection pooling.

Do not publicly expose conversation access without
implementing session verification and appropriate
conversation access controls.

### Testing

Requires local PostgreSQL.

Run:

python -m pytest tests/test_conversation_repository.py -v

Integration tests roll back temporary database
changes after execution.
