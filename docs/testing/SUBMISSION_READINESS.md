# Submission readiness — 10 October 2026

## Phase A audit (before application changes)

- Existing v.01 work preserved; v.02 not accessed. Existing 07C.1 grounding evaluator and tests retained.
- Backend baseline: **163 passed**, one existing Starlette/HTTPX deprecation warning.
- Python `compileall app`: passed. `pip check`: no broken requirements.
- PostgreSQL connected; pgvector **0.8.6** installed.
- Migrations 001/002 present and applied. **19 records / 19 embeddings**: events.csv 3, policies.csv 9, directory.json 7.
- HTTP smoke on isolated port 5051 with `GEMINI_ENABLED=false`: health, POL-003 retrieval, create, generation-unavailable response shape, contextual follow-up and exact original-question/source restoration passed.
- Root environment audited by variable presence only; no secrets printed. PostgreSQL/Gemini configuration exists; no Calendar/Web/Mailtrap integration configuration or LangGraph installation existed.
- No agent routes, tool adapters or implemented verification pipeline existed. Domain models alone do not constitute an agent.
- Public Office Holidays iCalendar source returned HTTP 200. The government web reference returned HTTP 500 and cannot be treated as connected; another real reference API is being verified.

## Initial deployment blockers

- No publicly deployed URL, no deployment configuration, no explicit production CORS.
- No public session isolation / conversation ownership or server-side provider quotas.
- Default localhost database config requires production `DATABASE_URL` with TLS.
- Embedding model initialized lazily; cold downloads and limited free-service memory require explicit cache and thread configuration.
- Root-relative structured-file paths are compatible with deployment of the whole repository, but would fail if only backend files were deployed.
- No production migration runner or indexing startup procedure.
- Background agent execution, persisted runs, results and CSV export absent.
- No email credentials: a third real tool connection cannot be claimed until a sandbox inbox is configured and exercised.

## Feature status at audit

| Feature | Evidence | Initial status |
| --- | --- | --- |
| Three structured documents, embeddings, semantic retrieval | 19 DB rows and 163 tests | Working locally |
| Prompt/query transformation and event context | HTTP contextual follow-up and stored query plan | Working locally |
| Cited Gemini answers | Existing backend implementation and prior documented live verification | Implemented; disabled for current regression |
| Original wording and history | Real HTTP restore | Working locally |
| React knowledge workspace | Existing frontend build/tests from prior implementation | Working locally |
| Public web interface | No deployed URL | Requires deployment |
| Calendar / Email / Web orchestration | Empty agent/integration directories | Missing at audit |
| Normalization / deduplication / verification / discrepancy export | No execution pipeline | Missing at audit |
| Production demo isolation and quotas | No middleware/session ownership | Missing at audit |

Final implementation and validation evidence will be appended after phases B–D. No automated regression test will issue live Gemini requests.

## Final implementation — phases B–D

| Feature | Evidence | Final status |
| --- | --- | --- |
| Reviewer entry and unified shell | Working `/signin`, five routes, collapsed/mobile navigation | Implemented; anonymous demonstration, not authentication |
| Knowledge Assistant / Evidence / Context / history | Real POL-003 retrieval, inherited EVT-101, exact restore; generated-answer/citation fixture tests | Working locally; successful live Gemini previously verified, no new provider request |
| Knowledge Sources | Actual PostgreSQL 19 records across 3 sources | Working locally; no upload endpoint/action |
| Calendar | Real HTTPS Office Holidays iCalendar read, persisted completed step | Live verified locally |
| Web | Real HTTPS Nager.Date API read, persisted completed step | Live verified locally |
| Email | Actual Mailtrap message/body adapter and official API contract; mocked transport tests | **Not connected**; server credentials required; no live claim |
| Autonomous orchestration | Bounded LangGraph StateGraph and persisted step states | Implemented; deterministic sequential workflow, not LLM planning |
| Extraction / normalization / deduplication | ICS/plain-text/JSON/HTML parsing, ambiguity/conflict tests, 11 duplicates in real run | Implemented with documented narrow supported formats |
| Reference verification | Indexed event/directory matching; active/registration/schedule checks | Implemented; live holiday claims correctly flagged, positive verification is fixture-tested |
| Results / history / CSV | Real persisted 16-record result, actual CSV, restored graph; formula mitigation | Working locally |
| Public session isolation / CORS / budgets | Real distinct-token denial, exact-origin preflight, 16 KB denial, durable budget tests | Locally verified production profile; not genuine identity authentication |
| Deployment startup / migrations / indexing | `render.yaml`, start script, fresh isolated database 3 migrations + 19 embeddings | Prepared and tested locally; hosted SSL/cold-start/memory/persistence outstanding |
| Public application URL | No deployment account operation performed | **Owner deployment required** |
| Media | 7 actual local PNGs and actual CSV in docs/submission | Created; no recording yet |

### Exact final validation

- Initial suite before code changes: **163 passed**, one existing deprecation warning.
- Expanded backend suite: **184 passed in 1.34s**, no reported warning in the final run. No live Gemini/provider call in regression tests; transport/adapters are explicitly mocked.
- Python compilation: passed. `pip check`: **No broken requirements found**. Selected new-code Ruff checks (F/E9/I): passed.
- Frontend production build: passed (208 modules; approximately 477 KB JS / 153 KB gzip, 39 KB CSS / 8 KB gzip).
- API client suite: **8 passed**.
- Browser suite against actual public-mode backend: **13 passed in 8.6s**. Includes reviewer entry, source counts, all four generation fixture states, validation/network paths, public-token history restore, actual read-only Calendar/Web, persisted discrepancy inspection, CSV download and reopened execution graph.
- Fresh isolated PostgreSQL database: all **3 numbered migrations applied**, **19 validated / 19 indexed records**, then temporary database removed. Existing assessment data not removed.
- HTTP public-profile probes: anonymous requests rejected, distinct reviewer conversations isolated, trusted origin accepted, untrusted origin rejected, oversized request denied.
- Public generation budget also covers Pydantic boolean coercion (`true`, `"true"`, `"yes"`, `1`), preventing quota bypass. No live generation request was made.
- Dependency installation audit: **0 frontend vulnerabilities** after adding React Flow; backend dependency consistency passed. This is not a claim that a comprehensive vulnerability scan of Python dependencies was performed.
- Git whitespace check: passed. No commit or push made.

### Actual journey outcomes

**Journey A:** Reviewer entry, persistent creation, EVT-101 question, contextual original follow-up, POL-003 source reference, reload and UUID reopening passed. Requested generation returned `unavailable` on the explicitly Gemini-disabled server; no answer message was invented. Latest browser verification conversation: `52e447d3-a49b-4aa0-971e-153f429a8669`.

**Journey B:** Real Calendar/Web requests completed; Email was skipped for absent Mailtrap credentials. Extraction, normalization, deduplication, verification, discrepancy handling and persistence completed. Results: **16 total, 0 verified, 16 flagged, 11 duplicates merged**. Unknown EVT references are flagged because the default sources describe genuine holidays, not the fictional assessment events. CSV export and history reload completed. Latest public-mode browser run: `a291adfe-1736-4e41-854c-cbf65a50ef89`. Full three-tool completion remains blocked solely by email configuration/activation, with extraction format limitations documented.

No fixture data is injected into these live records. Mocked Mailtrap reads, positive verified rows, inactive/unregistered cases, duplicate conflicts and generated answers are explicitly test-only coverage.

### Remaining owner actions and limitations

1. Configure a dedicated synthetic Mailtrap Email Testing inbox and run a live Email read. Until then, report **two** live connected tool categories.
2. Deploy the static frontend, Free Python service and pgvector PostgreSQL; set TLS `DATABASE_URL`, exact `FRONTEND_ORIGINS`, `DEMO_MODE=true`, `APP_ENV=production`, frontend `VITE_API_BASE_URL`, and verify billing/plan constraints. Exact steps are in docs/deployment/README.md.
3. Verify hosted memory, model-download/cold starts, cross-origin integration, database persistence after redeploy and the actual public URL. Local success is not hosted evidence.
4. Keep Gemini disabled for automation. Enable only for a deliberate manual grounded-answer demo after confirming provider project constraints.
5. Record/upload a real walkthrough and add its link. No recording exists yet.

FastAPI BackgroundTasks is not a resumable queue. Interrupted executions are marked failed on subsequent read after ten minutes. Synthetic demo-token isolation is not production identity; confidential data, stronger abuse protection, backups/retention and durable workers require additional hardening.

### Changed/new file groups

- Frontend: React/Vite configuration, package/lock files, shared shell, reviewer entry, KnowledgeAssistant, AgentWorkspace, KnowledgeSources, Evidence/Exchange, native-fetch API, responsive styles, API/browser tests and README/env example.
- Backend additions: `agents/workflow.py`, `integrations/tools.py`, `verification/pipeline.py`, `services/agent_repository.py`, agent/knowledge APIs, `core/demo.py`, `core/migrate.py`, module READMEs, three new test modules and dependency lock.
- Backend adaptations: router/CORS/public guard wiring in main.py; optional session scope in conversation repository/dependency; SSL env support in database.py; configurable embedding cache/thread count. Original request/response models and RAG/generation/evaluation logic remain intact.
- Infrastructure/docs: additive migration 003, render.yaml, scripts/start-backend.sh, root/frontend/backend/deployment READMEs, env examples, gitignore and actual submission PNG/CSV artifacts. Existing migrations 001/002 and Milestone 07C.1 evaluator/tests are unchanged. v.02 was not accessed or modified.

## Mailtrap activation follow-up — 2026-10-10

This supersedes the historical “Email not connected” status above. The existing adapter was inspected and executed against the configured root `.env`: account 2853336, sandbox 4953522, **real HTTPS HTTP 200, zero messages**. The token was not printed. FastAPI loads root environment configuration at startup; restart existing processes after changing credentials. The adapter correctly distinguishes a successful empty list from configuration, HTTP, timeout and malformed-response failures.

- Prepared controlled synthetic EVT-101 email and official Mailtrap Sandbox insertion instructions: [MAILTRAP_INTEGRATION.md](MAILTRAP_INTEGRATION.md). No message was sent by Codex.
- Added one opt-in live integration test, bounded to one message/two GETs, using the existing pipeline and actual PostgreSQL references/results. Calendar/Web and export are deliberately skipped in this email-only probe. No Gemini or frontend changes.
- Executed live probe: **1 skipped in 0.47s**, explicitly because the connected inbox is empty; no execution created. Message extraction/normalization/verification/persistence is **pending insertion**, not claimed as live verified.
- Regression suite with local PostgreSQL access: **191 passed, 1 skipped in 1.48s**. New unit coverage checks empty inbox, 401/403/503, timeout, invalid payload and controlled-message discrepancies. Selected Ruff F/E9/I checks and `git diff --check` passed. The first sandboxed regression attempt could not access local PostgreSQL; rerun with permitted local access passed.
- No commit/push, new provider, frontend rebuild, reference-data change or automatic email sending.
