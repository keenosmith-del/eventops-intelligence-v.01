# EventOps Intelligence — Data

## Purpose

This directory contains structured synthetic business
data and integration fixtures for EventOps Intelligence.

All participant information and business events are fictional and created for technical demonstration.

## Structured Knowledge Base

### events.csv

Authoritative event specifications.

Includes:

- Event identifiers
- Event names
- Start and end times
- Locations
- Capacity

### policies.csv

Authoritative operational and registration policies.

Includes:

- Policy identifiers
- Event-specific or global applicability
- Policy categories
- Business rules

The value ALL indicates global policy applicability.

### directory.json

Authoritative participant reference directory.

Includes:

- Participant identifiers
- Names and email addresses
- Organizations
- Active or inactive status
- Registered event identifiers

## Data Relationships

Events are identified using EVT-\* identifiers.

Policies reference specific events or apply globally.

Participants reference events through registered_events.

These relationships support cross-document retrieval
and subsequent agent verification.

## Source Authority

See:

docs/decisions/ADR-001-source-authority.md

Authoritative business data must remain separate from
supporting external evidence.

## Planned Integration Fixtures

The fixtures directory will contain synthetic data
representing:

- Google Calendar invitations
- Gmail registration messages
- Public directory API responses

Fixtures will include controlled inconsistencies:

- Duplicate registrations
- Missing contact information
- Inactive participant records
- Conflicting organization details
- Unknown attendees
- Incomplete registration messages

These will support repeatable tests before connecting
real Google APIs.

## RAG Ingestion

The ingestion pipeline will:

1. Read the structured documents.
2. Validate records and relationships.
3. Generate meaningful record-based knowledge chunks.
4. Preserve document and record metadata.
5. Create embeddings.
6. Make records available for semantic retrieval.

Ingestion and embedding generation are not yet implemented.

## Data Safety

No real personal information is required.

Do not commit real emails, OAuth credentials, access
tokens, or confidential business information.
