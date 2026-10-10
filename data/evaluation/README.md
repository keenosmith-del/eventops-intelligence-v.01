# RAG Retrieval Evaluation

## Purpose

This directory contains reproducible evaluation questions
for the EventOps Intelligence knowledge retrieval system.

## Dataset

rag_questions.json contains 13 evaluation cases.

The questions cover:

- Event lookup
- Paraphrasing
- Policy retrieval
- Global and event-specific rules
- Participant filtering
- Multi-record retrieval
- Unknown event identifiers
- No-matching-record scenarios
- Misleading status questions

## Expected Evidence

Each case identifies the source record IDs required
to support the question.

An empty expected_record_ids array means the retrieval
system should return no evidence.

## Evaluation Metrics

- Pass rate
- Recall@K
- Mean Reciprocal Rank
- Negative-case accuracy

These metrics measure evidence retrieval, not
natural-language answer correctness.

Additional retrieved records are not counted as failures
for positive cases. This limitation will be evaluated
separately when building answer grounding.

## Run Evaluation

From backend/:

python -m app.rag.evaluation

The evaluation runs against the actual local
FastEmbed model and structured knowledge records.

No paid AI API is required.

## Known Limitations

Questions asking whether a named person has a given
status may incorrectly apply that status as a filter.

This can exclude the person's authoritative record.

The evaluation suite includes a case to expose this
behaviour so the query-planning layer can be improved.

Multi-event comparisons and generation quality are
not yet assessed.

## Status-Verification Regression

EVAL-013 originally exposed a query-planning defect.

The question "Is Lindi Mokoena active for EVT-101?"
was incorrectly interpreted as a request to retrieve
only active participants.

This excluded the authoritative inactive participant
record P-003.

The query interpreter now distinguishes supported
status-verification questions from status-filtering
questions.

Status-verification questions retrieve evidence
without pre-filtering by the status being tested.

This prevents contradictory evidence from being
discarded before retrieval.

Named-person entity resolution and more complete
natural-language interpretation remain future
improvements.
