# ADR-002 — Grounded Generation and Cost Controls

**Status:** Accepted for local demonstration

## Context

EventOps Intelligence requires natural-language
answers grounded in structured source evidence.

The assessment must be demonstrated without
introducing paid API or cloud operating costs.

## Decision

Implement a separately controlled Gemini generation
service using gemini-3.5-flash-lite.

Keep retrieval, source verification and generation
as independently testable components.

Generation is disabled unless explicitly enabled.

Use only a dedicated, verified Free Tier Gemini
project with no associated billing account.

Reject unsupported citation identifiers.

Do not invoke provider tools, automatic retries
or paid-model fallbacks.

## Consequences

The application can run its retrieval workflow
without any Gemini calls.

The generation provider can be tested entirely
through mocked HTTP requests.

The model may fail or become unavailable when
free-tier limits are reached.

The backend must preserve retrieved evidence even
when answer generation is unavailable.

## Risks and Limitations

Free-tier availability and rate limits may change.

Application request limits do not independently
enforce Google's project billing status.

Free-tier usage has different data handling
conditions from paid-tier usage.

Valid citations do not automatically establish
that every claim in an answer is factually supported.

Before public deployment, implement access control,
rate limiting, usage auditing, stronger grounding
evaluation and provider-error observability.

## Verification

- Mocked provider responses
- Model restriction
- Provider disabled by default
- Missing-key failure
- Empty-evidence abstention
- Source-citation identifier validation
- No automatic retry on HTTP 429
  EOF
