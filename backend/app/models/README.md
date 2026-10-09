# Domain Models

## Purpose

This module defines the core Pydantic data contracts
used by EventOps Intelligence.

The models establish consistent structures between
the API, RAG engine, AI agent, external integrations
and verification services.

These are application-level contracts, not database
table definitions.

## Core Entities

| Model              | Responsibility                            |
| ------------------ | ----------------------------------------- |
| Event              | Event schedules and business information  |
| Registration       | Participant registration data             |
| KnowledgeRecord    | Structured content for RAG retrieval      |
| SourceEvidence     | Original source references and provenance |
| AgentRun           | Agent execution lifecycle                 |
| VerificationResult | Reconciliation outcomes and discrepancies |

## Validation

All domain models inherit from DomainModel.

Common rules:

- Unknown fields are rejected.
- Leading and trailing string whitespace is removed.
- Required identifiers cannot be empty.

Additional rules:

- Events require valid chronological schedules and
  timezone-aware timestamps.
- Event capacity must be greater than zero.
- Registrations can contain missing information.
- Verified results require evidence references.
- Verified results cannot contain unresolved issues.

## Engineering Decisions

### Separate data validation from business verification

Pydantic verifies the structure of application data.

Actual participant verification is handled separately
by deterministic business rules.

### Preserve provenance

Knowledge records and source evidence maintain
identifiers so answers and decisions can be traced
back to original source records.

### Support incomplete external data

Registration fields may be absent because external
calendar and email information is often incomplete.

Missing values are evaluated during reconciliation
instead of being silently fabricated.

### Define explicit workflow states

AgentRunStatus and VerificationStatus restrict
the application to known execution and decision states.

## Current Limitations

- Models are not yet persisted in PostgreSQL.
- Cross-record relationships are not yet validated.
- Registration normalization is not yet implemented.
- Source authority is not yet evaluated.
- Agent state transitions are not yet enforced.
- Evidence authenticity is not yet verified.

These behaviours will be added through dedicated
services, persistence and integration layers.

## Testing

From the backend directory:

python -m pytest tests/test_domain_models.py -v
