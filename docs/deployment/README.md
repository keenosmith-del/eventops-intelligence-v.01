# EventOps deployment

Preparation verified **11 October 2026 (Africa/Johannesburg)**. Public deployment is **blocked at Neon account authorization**. No EventOps cloud resources or verified public URLs exist. See [deployment evidence](DEPLOYMENT_STATUS.md) and the [release checklist](PRODUCTION_CHECKLIST.md).

## Architecture and isolation

| Component | Local development | Public assessment deployment |
| --- | --- | --- |
| React/Vite | 127.0.0.1:5173, npm run dev, existing proxy | Render Static Site, frontend/dist, public HTTPS API |
| FastAPI | 127.0.0.1:5050, existing reload command | Render Free Python service, Python 3.12.15, one worker, 0.0.0.0:$PORT |
| PostgreSQL | Docker PostgreSQL 17/pgvector, 127.0.0.1:55432, existing volume | Independent Neon Free project, PostgreSQL 17, TLS and pgvector |
| Configuration | Ignored root .env, existing credentials | Separate Render environment; production never reads developer dotenv files |
| Durable data | Local PostgreSQL | Neon knowledge/embeddings, conversations, sessions/ownership/quotas, runs/steps/results, n8n ledger |
| Model cache | Existing developer cache | /tmp/eventops-models, disposable and re-downloadable |

The approved UI and routes are unchanged. No local service requires Neon or Render. No production secret belongs in Vite, GitHub Actions or committed files. No local conversations, credentials or test executions are copied to production. Runtime uploads are not implemented; there is no filesystem upload store to migrate.

## Exact account setup and deployment fields

1. Complete **Neon Console** GitHub authorization in the pending Chrome tab. It requests read-only email addresses. The computer-use policy requires the owner to approve the new grant. Complete any signup terms yourself. Create an independent **Free** project, suggested name `eventops-intelligence-production`, select PostgreSQL **17** and a production database/role. Do not choose a trial, upgrade, attach payment information or reuse unrelated data. Verify current Free quotas; stop if free provisioning is unavailable.
2. Obtain a TLS PostgreSQL URL from Neon Connection Details. Prefer the **direct endpoint** for this small single-worker service and serialized migration transactions. Paste it only into Render's secure `DATABASE_URL` field. The role needs permission to create the vector extension/tables. Keep backups/exports secure; inspect the actual project's Free recovery retention before relying on it.
3. Review and intentionally commit/push the complete working v.01 implementation and deployment changes to GitHub **main**. Existing uncommitted Part 2 code/tests/n8n documentation are required for the tested implementation. Pushing only a subset can change behavior or fail CI. Git SSH access works; the separate gh token is invalid. Use normal Git SSH, or `gh auth login -h github.com` for CLI API operations. No commit/push was made by this task.
4. Render is already signed in and its existing GitHub integration lists **keenosmith-del/eventops-intelligence-v.01**. Use New → Blueprint → the connected repository, branch main, path render.yaml. Do not use the public-repository URL fallback: it does not provide automatic deployment. The draft form was inspected but not submitted; reload after pushing the prepared YAML.
5. The updated Blueprint creates only a **Free Python web service** and a **static site**: no database, disk or paid service. Supply DATABASE_URL, FRONTEND_ORIGINS and VITE_API_BASE_URL. Optional Gemini/Mailtrap keys are absent from mandatory prompts; add later to backend Environment only when intended. Verify the actual plans and workspace spending controls before final submission. New security grants/public provisioning require action-time confirmation under the computer-use policy.
6. Backend: root directory **blank** (whole repository), build `pip install -r backend/requirements.lock.txt`, start `bash scripts/start-backend.sh`, health-check `/ready`, branch main, **After CI Checks Pass**. A backend-only root excludes required data/migrations/scripts.
7. Frontend: root directory **blank**, build `bash scripts/build-frontend.sh`, publish `frontend/dist`, Node **24**, branch main, **After CI Checks Pass**. SPA rewrite `/* → /index.html` is included.
8. Set the actual assigned HTTPS frontend origin in FRONTEND_ORIGINS and HTTPS backend origin in VITE_API_BASE_URL. No wildcard, credentials or URL paths. If assigned hostnames contain suffixes, update both and redeploy/rebuild. The frontend hosted build refuses a missing/invalid API URL; backend production refuses missing/insecure configuration.
9. Wait for CI and both deployments, perform the hosted checklist, then record actual verified URLs in root README/status. A Render Live badge is insufficient.

Official references checked 11 October 2026: [Blueprint specification](https://render.com/docs/blueprint-spec), [CI-based deployments](https://render.com/docs/deploys), [Render Free constraints](https://render.com/docs/free), [Neon Free plan](https://neon.com/docs/introduction/free-tier), [Neon pgvector](https://neon.com/docs/extensions/pgvector). Current account plan/billing screens govern provisioning. Free Render PostgreSQL expires and is not used; Neon holds independent durable data.

## Environment inventory (no secret values)

| Variables | Location / purpose |
| --- | --- |
| POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT | Local root .env; retain Docker credentials/port 55432 |
| APP_ENV | Backend hosting: production activates dotenv isolation, TLS/origin guards, model warm-up and disables Swagger/OpenAPI pages; omit locally |
| DATABASE_URL, POSTGRES_SSLMODE | Backend production only: dedicated Neon URL and required TLS |
| DEMO_MODE, FRONTEND_ORIGINS | Backend production demo access and exact HTTPS origins; retain local defaults |
| DEMO_SESSION_LIMIT, DEMO_REQUEST_LIMIT, DEMO_WRITE_LIMIT, AGENT_DAILY_RUN_LIMIT | Backend PostgreSQL daily budgets; existing bounded defaults in Blueprint |
| GEMINI_ENABLED, GEMINI_API_KEY, GEMINI_DAILY_LIMIT | Backend only; disabled initially/in CI, separately approved production project/key |
| MAILTRAP_API_TOKEN, MAILTRAP_ACCOUNT_ID, MAILTRAP_INBOX_ID | Optional backend-only production sandbox, synthetic data, HTTPS read only |
| CALENDAR_FEED_URL, WEB_SOURCE_URL | Backend-only validated public HTTPS sources; cannot be chosen in reviewer requests |
| EMBEDDING_THREADS, FASTEMBED_CACHE_PATH, TOKENIZERS_PARALLELISM | Backend resource controls; one thread, disposable cache; startup disables tokenizer parallelism |
| LANGSMITH_TRACING | Disabled; external tracing not required |
| N8N_SERVICE_TOKEN, N8N_DAILY_RUN_LIMIT | Optional backend service integration; absent by default, independent of reviewer tokens |
| VITE_API_BASE_URL | Public frontend build setting only; empty locally for existing proxy |
| API_PROXY_TARGET | Optional local proxy override; default remains port 5050 |
| PYTHON_VERSION, NODE_VERSION, PORT, RENDER_GIT_COMMIT | Hosting/runtime; Render supplies port/release SHA |
| TEST_PREVIEW, TEST_PREVIEW_PORT, TEST_BASE_URL, PLAYWRIGHT_CHANNEL, RUN_LIVE_API, RUN_LIVE_ENTRY, RUN_MAILTRAP_LIVE | Test controls only; CI uses built frontend/fixtures with live opt-ins disabled |

Provider environment settings survive code releases. sync:false entries are supplied securely rather than committed. Vite changes require a rebuild; backend environment changes require redeployment. Avoid Blueprint edits that overwrite intentionally configured production options. Generation remains disabled until an independently free/unbilled project is approved; no automated check calls Gemini. Do not copy local provider secrets automatically.

## Database initialization and updates

Startup validates configuration, runs `python -m app.core.migrate`, runs `python -m app.rag.indexing`, then starts Uvicorn. Migrations 001–004 run transactionally under a PostgreSQL advisory lock and schema_migrations ledger. They create vector/vector(384), knowledge indexes, conversations/messages, sessions/ownership/budgets, agent runs/steps and the n8n delivery ledger. No reset is required.

Indexing reads only events.csv, policies.csv and directory.json: **19 records/19 embeddings**. Identity/fingerprint upserts regenerate only new/changed content. Repeated initialization produced zero changes/zero pending embeddings and preserved unrelated state. The model remains **BAAI/bge-small-en-v1.5**, 384 dimensions; no replacement or schema change was made.

Add new numbered additive SQL for future changes. Never edit applied migrations, delete the ledger, drop tables or reset hosted data. Keep changes compatible with the previously live release, because startup migrations precede traffic switching. Back up securely before changes. Inspect sanitized logs and fix forward after failure; source updates intentionally refresh affected embeddings without clearing reviewer history.

Verify through the Neon SQL editor without displaying connection credentials:

```sql
SELECT extversion FROM pg_extension WHERE extname = 'vector';
SELECT name FROM schema_migrations ORDER BY name;
SELECT COUNT(*) AS records, COUNT(embedding) AS embeddings,
       COUNT(DISTINCT document_id) AS documents FROM knowledge_records;
SELECT DISTINCT vector_dims(embedding) FROM knowledge_records WHERE embedding IS NOT NULL;
SELECT indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY indexname;
```

Expected baseline: four migrations, 19 records/embeddings, three documents, dimensions 384. Exact pgvector retrieval suits 19 records; an ANN index is not required. Never dump reviewer tokens/conversations into deployment logs.

## Automatic updates

Local edits → intentional commit/push to main → **Deployment checks** GitHub Actions → Render checksPass → frontend/backend releases. CI installs locked dependencies on Linux and runs pip check, initializes disposable PostgreSQL/pgvector, repeats migrations/indexing, runs backend tests, builds the frontend with a non-secret test API origin, runs unit tests and tests the production build in the browser with explicit fixtures. No production database, Gemini, Mailtrap or hosting credentials enter CI.

Both services follow main without path filters. Failed CI prevents automatic deployment once configured; this still needs hosted verification. Render can count neutral/skipped external checks as passed, so these CI jobs run on each main push without path skips. Check CI yourself before the first manual Blueprint deployment. The workflow/gate are prepared locally, **not activated or demonstrated remotely**. Manual deployments/environment edits need their own review.

Build/start logs identify RENDER_GIT_COMMIT. Compare the host release SHA with GitHub. Services deploy independently, so keep API changes compatible during rollout. Uncommitted edits do not reach production. Never reset the production database from CI.

## Hosted smoke checks

`/health` is process liveness. `/ready` checks database connectivity, migration baseline and complete indexing; it returns generic 503 on failure. Production startup loads the existing model before accepting traffic. Render uses `/ready`.

```bash
backend/.venv/bin/python scripts/smoke-production.py \
  --api https://YOUR-API.onrender.com \
  --frontend https://YOUR-FRONTEND.onrender.com
```

The bounded probe creates synthetic reviewer/conversation data, performs real retrieval/follow-up, checks POL-003 citations and session isolation, then restores through a fresh connection. It never requests generated answers. Add `--agent` for one intentional actual Calendar/Web execution, and `--require-email` only with a configured dedicated sandbox. Tool completion, CSV rows, persisted results/history are checked. It prints IDs, never tokens/provider exception bodies. Fresh connections alone do not prove redeploy survival.

Browser checks: landing/mascots, Start → reviewer → real session, five views, citations/context, individual conversation/execution routes, CSV and history. Refresh nested workspace/conversation/agents/verification/history/sources routes and inspect DevTools for JS/CORS failures. Keep the same reviewer tab, restart/redeploy backend and confirm identical evidence/results. Expired 24-hour access is not database loss. After idle spin-down, check health/readiness/source counts/retrieval. Push an intentional frontend update, check CI/release SHA/visible change and retained history. Record hosted checks only with actual URLs/timestamps/outcomes.

## Integration/security limits

Default Calendar/Web observations are real public holidays, unrelated to fictional EVT registrations; missing references must stay flagged. Configured variables are not connection proof. This task verified actual Calendar/Web reads locally through LangGraph. Mailtrap was disabled; earlier empty-inbox evidence cannot prove hosted connectivity/message processing. Gemini retains bounded generation/citation validation and opt-in behavior.

The [inactive n8n handoff](../../automations/n8n/README.md) and protected idempotent endpoints exist. Runtime import/credentials/webhook/cloud execution are unverified. No mandatory n8n service was added; LangGraph works independently.

Reviewer tokens are anonymous demo access, not commercial authentication. PostgreSQL stores token hashes, expiry/ownership and daily session/request/write/agent/Gemini quotas. Explicit CORS, request/source bounds, read-only HTTPS tools, private-address validation, no redirects, bounded reads, safe CSV and separate n8n service authorization remain active. Production disables Swagger/OpenAPI; public responses do not expose stack traces/credentials. No public admin/upload functionality was added.

Render Free has idle spin-down, ephemeral files, shared quotas and SMTP restrictions; Mailtrap uses HTTPS. No persistent paid disk is needed. BackgroundTasks persists transitions/results but **cannot resume interrupted runs**; reads mark runs older than ten minutes failed. Keep completed evidence and start a fresh intentional execution if required. Actual Free plan backup retention/recovery and usage limits must be inspected.

## Cold-start/memory evidence

An empty cache may download the unchanged model on initial indexing or production start. /tmp holds only reproducible model files. Indexing exits before serving, first serving initialization is serialized, documents embed in batches of four, and one worker/thread is used.

A clean **Linux amd64 Python 3.12.15 container constrained to 512 MB** downloaded the model and produced (19,384) documents/(384,) query after importing the real app. Peak process RSS **423,636 KiB (~414 MiB)**; download approximately 18 seconds on this connection. This is compatibility evidence, not a Render measurement/guarantee. Runtime/cgroup overhead, host networking and concurrency differ. Capture hosted cold-start/memory behavior. Investigate OOM without silently replacing the model/dimensions or enabling paid compute.

## Troubleshooting, logs and recovery

| Symptom | Action |
| --- | --- |
| Failed CI / no auto-deploy | GitHub Actions → Deployment checks; fix/push. Verify connected repo/main and After CI Checks Pass |
| Dependency/model startup failure | Render Events/build/Logs; verify exact Python/lock, writable cache and model download access |
| OOM | One worker/thread/bounded batches; inspect hosted evidence and discuss a verified free alternative before provider/model changes |
| TLS/database failure | Check dedicated Neon availability, direct TLS URL and role permissions; never paste/log URL |
| Health 200 / readiness 503 | Inspect migrations/connectivity/embeddings; liveness alone is insufficient |
| CORS / fetch failure | Exact backend origin in frontend build and frontend origin in backend; rebuild/redeploy |
| Nested route 404 | Static SPA rewrite /* → /index.html |
| Reviewer 401 / hidden history | Session expiry/ownership; never weaken isolation to restore objects |
| Partial run / Email skipped | Inspect actual step, configure sandbox if intended; empty/missing source is not successful registration ingestion |
| n8n 401/503 | Separate service credential/configuration; reviewer token cannot authorize it |
| ~505 KB JS build warning | Non-fatal existing bundle-size warning; no UI/code-splitting redesign introduced |

Render service **Events** shows release/build failures; **Logs** shows migrations/indexing/runtime, with release SHA. GitHub Actions holds CI logs. Neon console shows project usage/availability. Keep logs/screenshots free of secrets.

Rollback: temporarily disable auto-deploy and deploy the last known-good SHA using rollback/manual controls available to the actual account. Do not reset Neon: additive migrations remain applied and must support previous code. If incompatible, fix forward or restore a secure backup into a separate database after reviewing data-loss consequences. Coordinate frontend/backend rollback, re-enable checksPass and repeat smoke/persistence checks. Cloud backup/rollback capabilities were not verified in this task.
