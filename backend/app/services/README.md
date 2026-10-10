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
