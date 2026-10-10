# EventOps Intelligence v.01

Inference Group AI Engineering assessment: an integrated React workspace for structured RAG and bounded, observable event verification tooling. **v.02 is out of scope.**

## Current status

| Requirement | Actual implementation / evidence |
| --- | --- |
| Three structured documents, real embeddings, semantic retrieval | events.csv (3), policies.csv (9), directory.json (7); 19 persisted 384-dimensional embeddings, PostgreSQL/pgvector |
| Query transformation, context retention and citations | Existing deterministic RAG query/context pipeline; original wording, evidence and successful generated citations persist |
| Grounded generative answers | Existing optional Gemini integration; prior live verification documented in docs/testing/README.md; disabled by default and throughout this regression work |
| Polished web interface | `/signin`, five navigation views, Evidence/Context panel, React Flow graph, responsive layouts, real API integration |
| Calendar tool | Real public HTTPS iCalendar feed read, executed locally |
| Web tool | Real HTTPS reference API read, executed locally |
| Email tool | Real Mailtrap HTTPS read confirmed HTTP 200 with an empty inbox; controlled-message ingestion/persistence awaits insertion; [bounded live test and instructions](docs/testing/MAILTRAP_INTEGRATION.md) |
| Extraction, normalization, deduplication and verification | Deterministic LangGraph stages, reference comparisons, conflict/missing-field flags and provenance |
| Results, execution history and export | PostgreSQL runs/steps/results; selectable node/record detail; actual CSV download and history restoration verified |
| Public assessment controls | Anonymous demo-token isolation, explicit CORS, persistent quotas, input/source bounds, read-only tools |
| Public URL | **Not deployed**. Owner must configure accounts/credentials and deploy |

Calendar and Web have live record-processing evidence. Mailtrap now has a successful real HTTPS connection read, but its inbox is empty; three-source record-processing completion remains unverified. Default public holiday observations do not match the fictional EVT dataset; all 16 observed records in the earlier live run were correctly flagged, with 11 duplicates merged. Positive verified/inactive/conflicting cases are covered by explicit synthetic test inputs, not substituted into live runs.

## Quick local setup

Prerequisites: Python 3.12, Node 22.12+ or 24, npm, Docker Desktop.

```bash
cp .env.example .env
# Set your own local PostgreSQL password in the root .env.
docker compose up -d --wait db
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
python -m app.core.migrate
python -m app.rag.indexing
GEMINI_ENABLED=false python -m uvicorn app.main:app --reload --reload-dir app --host 127.0.0.1 --port 5050
```

In another terminal:

```bash
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

Open http://127.0.0.1:5173/signin and **Continue as reviewer**. This creates demonstration access, not genuine authentication; no personal credentials are needed. The backend reads the **root** `.env`. Local `DEMO_MODE=false` exposes the local synthetic dataset without session ownership enforcement. Public deployments must use `DEMO_MODE=true` and exact `FRONTEND_ORIGINS`; old unowned local conversations/runs then remain inaccessible to reviewers.

Vite proxies `/api` and `/health` to port 5050. `API_PROXY_TARGET` can select an isolated local test server. Production uses the public `VITE_API_BASE_URL`, which is embedded at build time. Provider keys and PostgreSQL credentials stay server-side.

## Walkthroughs

**Journey A:** Enter reviewer demo → create a conversation → ask “What time does check-in close for EVT-101?” → inspect POL-003 and the original policy reference → request optional Gemini generation (unavailable while disabled) → ask “What time does its check-in close?” → inspect inherited EVT-101 context → reopen history/UUID. Successful saved answers retain citations; unsuccessful generation outcomes are not persisted by the existing history API, and the UI explicitly reports that historical uncertainty.

**Journey B:** Open Agent Workspace → Run verification → observe real persisted stages → select Calendar/Email/Web steps → inspect normalization, duplicate counts and discrepancies → inspect a record's source/reference evidence → export all or verified-only CSV → reopen Execution History and restore graph state. Email is skipped until a real sandbox is configured. No external email is sent.

Knowledge Sources queries the actual indexed documents/counts/provenance. No fake upload action is present.

## Architecture

React/Vite + React Router + native fetch + React Flow → FastAPI → PostgreSQL/pgvector.

RAG: typed ingestion → local FastEmbed → persistent semantic retrieval → deterministic context/query resolution → optional bounded Gemini answer → citation validation → durable messages.

Agent: Trigger → Calendar → Email → Web → Extraction → Normalization → Deduplication → Verification → Discrepancy handling → Persistence → explicit CSV export. LangGraph executes the reads/checks autonomously after one trigger; this is a deterministic bounded workflow, not LLM-driven tool selection. Inputs, outputs, errors and timestamps are stored independently for each stage.

Authority remains the indexed event/directory records. Missing event IDs are not filled from the run target, inactive participants cannot become verified, and conflicts are reported rather than silently corrected. Source evidence is distinct from generated text and from deterministic verification decisions.

## Routes and APIs

Frontend routes: `/signin`, `/`, `/conversations/:uuid`, `/agents`, `/agents/runs/:uuid`, `/verification`, `/verification/:uuid`, `/history`, `/history/:uuid`, `/sources`.

Existing APIs remain: `GET /health`, `POST /api/rag/retrieve`, `POST/GET /api/conversations`, `GET /api/conversations/{uuid}`, `POST /api/conversations/{uuid}/messages`.

Additions: `POST /api/demo/session`, `GET /api/demo/config`, `GET /api/knowledge/sources`, `GET /api/agents/connections`, `POST/GET /api/agents/runs`, `GET /api/agents/runs/{uuid}`, `/results`, `/export.csv?verified_only=false`.

Interactive schemas: http://127.0.0.1:5050/docs. Message requests retain `question`, `top_k`, `generate_answer`; original backend data models/contracts were preserved. New SQL migration 003 is additive.

## Validation

```bash
cd backend
source .venv/bin/activate
GEMINI_ENABLED=false python -m pytest -q
python -m compileall -q app
python -m pip check
```

```bash
cd frontend
npm run build
npm test
npx playwright install chromium
npm run test:e2e
# Real local reads/persistence; backend MUST have generation disabled:
RUN_LIVE_API=true npm run test:e2e
# Or with installed Chrome:
PLAYWRIGHT_CHANNEL=chrome RUN_LIVE_API=true npm run test:e2e
```

Verified 10 October 2026: initial **163-test baseline**, expanded **184 backend tests**, **8 API client tests**, **13 browser tests** including real RAG and Calendar/Web agent journeys; build, compilation and dependency checks passed. Fresh isolated local database migration/indexing yielded 19/19 records/embeddings and three migrations. Exact-origin CORS, anonymous denial, separate reviewer isolation and request-size bounds passed HTTP checks. No live Gemini request was issued during this work. Hosted deployment checks remain outstanding.

Detailed evidence and blockers: [Submission readiness](docs/testing/SUBMISSION_READINESS.md).

## Deployment and remaining blockers

Follow [the exact deployment actions](docs/deployment/README.md). `render.yaml` prepares a Free Python service and static site without provisioning paid infrastructure; supply a persistent pgvector PostgreSQL URL with TLS. `scripts/start-backend.sh` applies migrations/indexes sources, then binds to `0.0.0.0:$PORT`. Cloud runtime does not depend on Docker.

The owner must deploy the public URL, configure the exact frontend/backend URLs and CORS, and insert the [controlled Mailtrap email](docs/testing/MAILTRAP_INTEGRATION.md) to verify live email record processing. Gemini should remain disabled for automated checks; manually enable it only after confirming provider account/billing constraints. Free-host memory/cold starts, hosted TLS connectivity and persistence after actual redeploy are not yet verified.

BackgroundTasks is not a durable queue: interrupted runs are marked failed on later read after ten minutes and do not resume. Demo tokens isolate synthetic assessment objects but are not production identity. Global daily budgets can be exhausted by anonymous traffic. Extraction supports specified ICS/JSON/plain-text patterns, not arbitrary attachments, OCR or general semantic reasoning. Further commercial authentication, retention, audit/claim evaluation and durable worker orchestration are outside this v.01 assessment increment.

## Submission evidence

Actual local artifacts: [agent desktop](docs/submission/screenshots/agent-execution-desktop.png), [agent mobile](docs/submission/screenshots/agent-execution-mobile.png), [CSV sample](docs/submission/sample-verification.csv). Additional real reviewer/RAG/source screenshots are listed in [screenshots README](docs/submission/screenshots/README.md).

- Public application URL: **[add after deployment]**
- Walkthrough recording: **[add actual recording link]** — no recording exists yet; prepared directory: `docs/submission/recordings/`.

Nothing is committed or pushed automatically. Setup/testing details: [frontend README](frontend/README.md), [backend README](backend/README.md), [agent module](backend/app/agents/README.md).
