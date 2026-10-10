# ADR-001 — Source Authority and Data Provenance

## Status

Accepted

## Context

EventOps Intelligence retrieves operational information
from structured documents, Google Calendar, Gmail, and external web resources.

These sources may contain incomplete, duplicated,
contradictory, or outdated information.

The system requires explicit rules to determine which
information can be considered authoritative.

## Decision

The application distinguishes source evidence from
verified business facts.

### Authoritative Sources

| Information                | Authoritative Source                   |
| -------------------------- | -------------------------------------- |
| Event specifications       | events.csv                             |
| Operational policies       | policies.csv                           |
| Participant identity       | directory.json                         |
| Participant account status | directory.json                         |
| Event eligibility          | directory.json and applicable policies |

### Supporting Sources

Google Calendar provides event invitations and attendee
information.

Gmail provides registration correspondence and claims.

A published web directory provides reference records
that can be checked against local structured data.

Calendar invitations and email messages are not
independently sufficient to establish verified eligibility.

## Verification Rules

- Preserve original source references.
- Normalize information before comparison.
- Do not invent missing fields.
- Flag contradictions instead of silently resolving them.
- An inactive participant must not be marked verified.
- Event registration must be supported by the directory.
- Unresolved conflicts require review.
- Model-generated interpretation cannot override deterministic business verification.

## RAG Implications

Every knowledge chunk must preserve:

- Document identifier
- Record identifier
- Original structured content
- Relevant event identifier
- Source metadata

Generated answers must use retrieved evidence.

When supporting evidence is absent, the system should communicate that the answer cannot be established.

## Consequences

This design improves explainability, auditability, and consistency.

It also requires explicit normalization, matching, provenance tracking, and handling of conflicting records.

## Current Scope

This decision currently governs fictional structured data used in the technical demonstration.

Live Google and web integrations will require additional checks for source freshness, permissions, and trust.
