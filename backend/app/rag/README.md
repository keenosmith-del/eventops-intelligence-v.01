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
