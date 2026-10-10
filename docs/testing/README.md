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
