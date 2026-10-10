# RAG — Retrieval-Augmented Generation

## Purpose

This module implements the structured knowledge ingestion
and retrieval components of EventOps Intelligence.

The knowledge base supports questions about events,
operational policies and participant reference data.

## Implemented Components

### ingestion.py

- CSV and JSON parsing
- Pydantic schema validation
- Cross-document reference validation
- Duplicate identifier detection
- Structure-aware knowledge chunking
- Source provenance metadata
- Deterministic source fingerprints

Entry point:

ingest_structured_documents(data_dir=None)

### embeddings.py

- Local FastEmbed inference
- BAAI/bge-small-en-v1.5 model
- Document embedding generation
- Query embedding generation
- Vector shape and numerical validation

Each embedding has 384 dimensions.

The model runs locally without a paid inference API.

### retrieval.py

- In-memory document vector index
- Cosine similarity ranking
- Record-type filtering
- Event-specific filtering
- Global policy inclusion
- Participant/event association filtering
- Source provenance preservation
- Deterministic ranking order for equal scores
- Authoritative event existence validation
- Unknown event filters return no records
- Global policies apply only to known events

Main class:

SemanticRetriever

Main method:

search(query, top_k=5, record_type=None, event_id=None)

## Data Flow

Structured documents
-> Schema validation
-> KnowledgeRecord generation
-> Local document embeddings
-> In-memory vector index
-> Query embedding
-> Cosine similarity
-> Optional metadata filtering
-> Ranked SearchHit results

## Source Documents

- events.csv
- policies.csv
- directory.json

The current knowledge base contains 19 records.

## Search Results

Each result contains:

- Original KnowledgeRecord
- Cosine similarity score
- Document identifier
- Record identifier
- Source reference
- Source fingerprint
- Business metadata

Similarity scores describe vector relevance,
not factual correctness or verification confidence.

## Performance

Document embeddings are generated when the retriever
is constructed.

The in-memory index is reused for subsequent searches.

Only the query embedding is regenerated for each search.

The current implementation uses linear search across
the indexed document vectors.

This is appropriate for the small demonstration dataset.

## Testing

Run:

python -m pytest tests/test_rag_ingestion.py -v

python -m pytest tests/test_rag_retrieval.py -v

The retrieval unit tests use controlled fake embeddings
to test ranking and validation without model inference.

Actual model relevance must be evaluated separately
using the local FastEmbed model.

## Current Limitations

- Vector index exists only in process memory.
- Embeddings are regenerated on process restart.
- No PostgreSQL or pgvector persistence yet.
- No automatic query transformation yet.
- No exact identifier extraction from free-text queries.
- No model-generated answers yet.
- No answer abstention logic yet.
- No conversation persistence yet.
- No retrieval relevance benchmark yet.

Top-ranked results must not automatically be treated
as sufficient evidence to answer a question.

## Next Phases

1. Evaluate actual retrieval relevance.
2. Add query classification and exact identifier handling.
3. Introduce persistent vector indexing.
4. Add retrieval evaluation datasets.
5. Integrate grounded Gemini generation.
6. Implement conversation persistence.

## Cost Constraint

All current ingestion and retrieval operations run
locally and incur no cloud API or inference charges.

## Query Understanding

Module: query.py

The query interpreter converts supported natural-language
questions into an explicit QueryPlan.

Supported capabilities:

- Extract event identifiers
- Normalize event identifiers
- Identify event, policy and participant questions
- Detect active/inactive participant conditions
- Detect selected policy categories
- Reject unsupported multi-event comparisons
- Preserve broad semantic retrieval when intent is unclear

The retrieval engine supports deterministic filtering
before similarity ranking.

Source records retain their original evidence metadata.

## Query Processing Limitations

The query interpreter is rule-based and currently supports
a defined set of operational question patterns.

It does not yet provide general-purpose intent recognition.

Unknown event identifiers produce no results.

An empty result set is not a verified negative business
finding; it means the current retrieval request found no
eligible evidence.

Semantic similarity alone is not sufficient to determine
whether a generated answer is supported.

Multi-document answer synthesis, confidence calibration
and response abstention will be addressed separately.

## Query Tests

python -m pytest tests/test_rag_query.py -v

## Retrieval Evaluation

Module: evaluation.py

Evaluation dataset:
data/evaluation/rag_questions.json

The evaluation measures:

- Case pass rate
- Recall@K
- Mean Reciprocal Rank
- Negative-case accuracy

Run:

python -m app.rag.evaluation

Automated evaluator tests:

python -m pytest tests/test_rag_evaluation.py -v

Evaluation currently measures retrieval quality only.
Generated answer grounding will be tested separately.

## Status-Verification Query Handling

Queries requesting participants with a particular
status use deterministic metadata filtering.

Questions asking whether a participant has a status
do not pre-filter records by the proposed status.

This allows retrieval of evidence that contradicts
a question's premise.

The behaviour is covered by query and retrieval
evaluation regression tests.

The current implementation does not yet guarantee
that named-person questions retrieve only the named
participant.

cat >> app/rag/README.md <<'EOF'

## Persistent Knowledge Indexing

Module: indexing.py

The indexing coordinator connects structured ingestion
to the PostgreSQL knowledge repository.

It performs:

1. Source document validation
2. Idempotent knowledge record upserts
3. Identification of missing embeddings
4. Local embedding generation
5. Persistent vector storage

Run:

python -m app.rag.indexing

Knowledge records and embeddings survive database
container restarts because PostgreSQL uses a
Docker-managed persistent volume.

The current semantic retriever still performs
in-memory similarity search.

Persistent pgvector retrieval will be implemented
in the next stage.
EOF

## PostgreSQL-Backed Semantic Retrieval

Module: postgres_retrieval.py

PostgresSemanticRetriever implements the same search
interface as the in-memory SemanticRetriever.

It queries persistent pgvector embeddings directly
inside PostgreSQL.

Features:
- Cosine-distance similarity ranking
- Local query embedding generation
- Event identifier validation
- Event-specific filtering
- Global policy inclusion
- Participant status filtering
- Policy category filtering
- Source provenance preservation
- Exclusion of records without embeddings

The implementation uses exact nearest-neighbour search.

No approximate vector index is necessary for the
current 19-record knowledge base.

## Retrieval Backend Interface

The SearchProvider protocol allows query interpretation
and evaluation to use either:

- SemanticRetriever (in-memory)
- PostgresSemanticRetriever (database-backed)

Both return SearchHit objects containing the original
KnowledgeRecord and a similarity score.

## Database Retrieval Testing

PostgreSQL must be running.

Run:

python -m pytest tests/test_postgres_retrieval.py -v

Tests use transaction rollback to preserve the
authoritative knowledge base.

## Current Limitations

- No approximate vector index
- No database connection pool
- No automatic concurrent indexing coordination
- Records without embeddings cannot be semantically ranked
- Query planning remains rule-based
- Named-person resolution is not yet complete
- Generated-answer grounding remains to be implemented

## Deterministic Conversation Context

Module: context.py

Resolves explicit event references in follow-up
questions using persistent conversation history.

### Supported Behaviour

- Preserves explicitly supplied event identifiers
- Resolves clear references such as "its"
- Supports "that event" and "the same event"
- Uses the most recent retrieval response
- Requires an unambiguous event identifier
- Requires supporting retrieval evidence
- Preserves the original user question
- Produces an enriched retrieval question

### Safety and Reliability

The resolver does not invent event identifiers.

If conversational context is missing or ambiguous,
a context-dependent question raises ValueError.

Context resolution is deterministic and uses
no external language model.

### Current Limitations

The initial implementation only resolves selected
event references.

It does not yet support:
- General pronoun and entity coreference
- Multi-event comparisons
- Person-name resolution
- Complex multi-turn reasoning
- LLM-assisted contextual interpretation

### Testing

python -m pytest tests/test_rag_context.py -v

The module will be integrated into the Conversation
API after its standalone tests have passed.

## Conversation API Integration

The deterministic context resolver is integrated
into POST /api/conversations/{id}/messages.

The resolver receives ordered messages loaded from
the PostgreSQL conversation repository.

The original question is preserved in the user message.

The enriched query and inherited event identifier are
stored with the assistant retrieval message.

Integration tests verify:
- Successful event inheritance
- Rejection of missing context
- Rejection of ambiguous context
- Explicit event identifiers taking precedence
- Persistent conversation history

Context resolution runs before local query embedding
and pgvector similarity search.
