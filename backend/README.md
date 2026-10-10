# EventOps Intelligence — FastAPI backend

Structured retrieval, context-aware persistent conversations, optional Gemini answers and a bounded LangGraph verification workflow. Existing domain/RAG contracts and the original 163-test suite are preserved; additive APIs/migration implement reviewer demo access and agent storage.

## Setup

Configure the root `.env` from `.env.example`, start PostgreSQL, then:

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
python -m app.core.migrate
python -m app.rag.indexing
GEMINI_ENABLED=false python -m uvicorn app.main:app --reload --reload-dir app --host 127.0.0.1 --port 5050
```

The migration runner applies numbered SQL once under an advisory lock. The first two migrations are unchanged and idempotently adopt an already prepared database; 003 adds agent/demo storage. Full repository files are needed for structured source indexing and migration discovery.

## APIs

Existing: `/health`, `/api/rag/retrieve`, `/api/conversations`, `/api/conversations/{uuid}`, `/api/conversations/{uuid}/messages`.

Additions:

| Route | Purpose |
| --- | --- |
| `POST /api/demo/session` | Anonymous 24-hour reviewer token, not authentication |
| `GET /api/demo/config` | Safe mode/generation-enabled flags |
| `GET /api/knowledge/sources` | Actual indexed records/counts/provenance |
| `GET /api/agents/connections` | Configuration availability; not a connectivity claim |
| `POST /api/agents/runs` | Accept bounded `{ event_id, max_records }`, stable UUID; BackgroundTasks starts graph |
| `GET /api/agents/runs` | Recent scoped executions |
| `GET /api/agents/runs/{uuid}` | Persisted state, step details and results |
| `GET /api/agents/runs/{uuid}/results` | Saved verified/flagged records |
| `GET /api/agents/runs/{uuid}/export.csv` | Actual CSV; optional `verified_only=true` |

Public mode requires `X-Demo-Session`, enforces ownership of conversation/run objects and uses durable daily quotas. Prior unowned local objects are not accessible to public reviewers. Exact frontend-origin CORS is configured via `FRONTEND_ORIGINS`. Production requires `DEMO_MODE=true`. No model/request contract was replaced.

RAG messages preserve `question`, `top_k`, `generate_answer`; response statuses are not_requested/generated/unavailable/insufficient_evidence. Successful answer citations persist, while unsuccessful generation status is not historical metadata. Gemini remains disabled by default and in regression tests. Existing citation verification is not complete claim-level semantic entailment.

## Agent scope

Real read-only Calendar (iCalendar), Web JSON/HTML and Mailtrap Email Testing adapters. The graph independently records extraction, normalization, deduplication, reference comparisons, discrepancy summary and persistence. Email is not connected until sandbox credentials are supplied. No email send API, SMTP or live-LLM agent planner is present. Missing source IDs are not guessed from a run's target event.

Results reference current indexed event/directory records; synthetic public holiday observations do not meet EVT authority criteria and remain flagged. Tests use explicit fixtures for positive verification, not runtime fallback data. [Agent details](app/agents/README.md), [integration details](app/integrations/README.md), [verification details](app/verification/README.md).

BackgroundTasks is not a durable job queue. Runs interrupted by a restart are marked failed after ten minutes on read, retaining completed step evidence. Genuine production identity, backups/retention and durable resumable workers remain outside this assessment increment.

## Validation and deployment

```bash
GEMINI_ENABLED=false python -m pytest -q
python -m compileall -q app
python -m pip check
```

Verified: **184 passed**, compilation passed, no broken dependencies. Original baseline: 163 passing tests. Added tests cover parser/normalizer, verified/inactive/unregistered/ambiguous/conflicting claims, mocked tool transports/failures, graph persistence, isolation, durable budgets and CSV safety. Fresh isolated PostgreSQL migration/indexing confirmed three migrations and 19 records/embeddings. Actual HTTP Calendar/Web execution, discrepancies, CSV and recovery passed.

`DATABASE_URL` supports URL-provided SSL parameters; `POSTGRES_SSLMODE` can explicitly override them and must require TLS for hosting. Model cache/thread settings are configurable. `scripts/start-backend.sh` performs migrations/indexing then binds `0.0.0.0:$PORT`, one worker. [Exact deployment actions](../docs/deployment/README.md) cover Free hosting constraints, public CORS, Mailtrap setup and outstanding hosted verification.
