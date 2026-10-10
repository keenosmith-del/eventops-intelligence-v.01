## RAG Retrieval Backend Comparison

### Implementations

1. In-memory NumPy cosine similarity
2. PostgreSQL pgvector cosine similarity

Both use:

- BAAI/bge-small-en-v1.5
- 384-dimensional local embeddings
- The same structured knowledge records
- The same deterministic query interpretation
- The same 13-case evaluation dataset

### Verified Results

| Metric           | In-memory | PostgreSQL |
| ---------------- | --------- | ---------- |
| Evaluation cases | 13        | 13         |
| Passing cases    | 13        | 13         |
| Pass rate        | 100%      | 100%       |
| Mean Recall@K    | 100%      | 100%       |
| MRR              | 1.0000    | 1.0000     |

PostgreSQL integration tests: 9 passed.
Complete backend suite: 89 passed.

Persistent database contents:

- 19 knowledge records
- 19 stored embeddings

### Interpretation

Both implementations retrieved all expected source
records within the evaluation's top-K limits.

PostgreSQL performs similarity ranking against
persisted pgvector embeddings rather than rebuilding
document embeddings for each retriever instance.

### Limitations

These results apply only to the current evaluation set.

Positive cases may contain additional irrelevant records.

The benchmark does not measure generated-answer
correctness, hallucination rates, or agent performance.

Broader evaluation and answer-grounding tests remain
necessary before submission.

## Milestone 07B — Live Gemini RAG Integration

### Verification

Status: PASSED
Date: 2026-10-10

Model: gemini-3.5-flash-lite

The complete RAG workflow was verified using real
local embeddings, PostgreSQL, pgvector and Gemini.

### Tested Workflow

1. Create a persistent RAG conversation.
2. Submit a natural-language question.
3. Interpret and filter the question.
4. Generate the local query embedding.
5. Retrieve evidence from PostgreSQL.
6. Generate a grounded answer through Gemini.
7. Validate the returned citation identifier.
8. Persist question, retrieval and answer messages.
9. Reload the conversation from PostgreSQL.

### Test Question

What time does check-in close for EVT-101?

### Verified Result

Generation status: generated

Answer:
Check-in for EVT-101 closes at 08:45
South Africa Standard Time.

Evidence:
POL-003

Source:
data/structured/policies.csv#policy_id=POL-003

### Persistence

Three messages were successfully saved and recovered:

- User question
- Assistant retrieval evidence
- Assistant generated answer

### Cost Controls

- Dedicated AI Studio Free Tier project
- Fixed Gemini model
- One generation request per operation
- No automatic retries
- No paid-model fallback
- Bounded output tokens
- Backend-only API key
- Generation disabled by default

Google Cloud Billing linkage was not independently
verified because account authentication was unavailable.

### Limitations

This verifies one live question and answer.

It does not establish overall answer accuracy,
claim-level grounding reliability, or performance
across more complex questions.

Additional grounding evaluations remain necessary.
