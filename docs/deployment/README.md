# Deployment — EventOps Intelligence v.01

Status: configuration and local production-profile verification are implemented. **No public deployment or URL has been created.** Provider accounts, credentials and plan limits must be configured by the owner. v.02 is out of scope.

## Supported assessment topology

- React/Vite static site on Render Static Sites (or another static host).
- FastAPI Python web service on Render's **Free** plan, one worker.
- External persistent PostgreSQL with pgvector, for example a **Neon Free** project.
- Optional Gemini, disabled initially.
- Public remote iCalendar feed + HTTPS reference API; optional Mailtrap **Email Testing sandbox** read integration.

`render.yaml` defines a Free Python service and a static site. It creates **no paid service, database or provider account**. Configure placeholder environment entries in the dashboard before deployment. It cannot independently verify billing settings or guarantee quotas will remain available.

Provider constraints, checked 10 October 2026: [Render Free documentation](https://render.com/docs/free) describes idle spin-down, ephemeral filesystems and outbound SMTP restrictions. Free Render PostgreSQL expires after 30 days, so it is not the recommended durable assessment database. [Neon plan documentation](https://neon.com/docs/introduction/free-tier) describes the Free plan; [Neon's pgvector documentation](https://neon.com/docs/extensions/pgvector) documents enabling the extension. Reconfirm plan limits in the account dashboard, do not enable automatic upgrades, and use a no-payment-method or hard spending-limit setup where supported.

## Exact owner actions

1. Review these changes, then commit/push **manually** to the v.01 repository. Nothing is committed or pushed automatically.
2. Create/select a **Free** PostgreSQL project supporting pgvector. Obtain its connection URL with `sslmode=require`. Do not paste it into a browser-side env variable or chat. The role must be allowed to create the vector extension and tables.
3. Import `render.yaml` as a Blueprint, or create equivalent services manually. Keep the backend on **Free**, Python 3.12, single worker. Set these backend variables:

   ```text
   APP_ENV=production
   DATABASE_URL=<provider PostgreSQL URL with sslmode=require>
   POSTGRES_SSLMODE=require
   DEMO_MODE=true
   FRONTEND_ORIGINS=https://<exact static-site hostname>
   GEMINI_ENABLED=false
   EMBEDDING_THREADS=1
   FASTEMBED_CACHE_PATH=/tmp/eventops-models
   LANGSMITH_TRACING=false
   ```

4. Set the frontend build variable `VITE_API_BASE_URL=https://<API hostname>`. Rebuild the static frontend after changing it. The static build command is `npm --prefix frontend ci && npm --prefix frontend run build`, publish directory `frontend/dist`. Add a SPA rewrite `/* → /index.html`; the Blueprint supplies it.
5. Redeploy the backend once the exact frontend URL is known. CORS accepts only configured origins, GET/POST and the `Content-Type`/`X-Demo-Session` headers. Public mode refuses to start without an explicit origin; production refuses to start with demo isolation disabled.
6. Backend build: `pip install -r backend/requirements.lock.txt`. Start: `bash scripts/start-backend.sh`. The script runs transactional numbered migrations, indexes the three authoritative source files, then binds Uvicorn to `0.0.0.0:$PORT`. It does not need Docker at runtime. Deploy the **whole repository** so `data/structured/` and SQL migrations exist.
7. Verify `/health`, open `/signin`, continue as reviewer and run both walkthroughs. Confirm cross-origin access, conversation/run isolation, POL-003 evidence, CSV download and persistence after restarting the service. These final hosted checks have **not** been executed locally.
8. To activate the third tool, configure a dedicated Mailtrap Email Testing sandbox containing only synthetic assessment registrations:

   ```text
   MAILTRAP_API_TOKEN=<sandbox read token>
   MAILTRAP_ACCOUNT_ID=<numeric account ID>
   MAILTRAP_INBOX_ID=<numeric inbox ID>
   ```

   Use [Mailtrap's messages API](https://docs.mailtrap.io/developers/email-sandbox/messages/get-messages) and [plain-text body API](https://docs.mailtrap.io/developers/email-sandbox/messages/get-text-message). A configured token alone is not evidence of a working connection: run verification, inspect the Email step and its provenance, and confirm actual body extraction. Until this is done, Part 2 has **two live connected tool categories, not three**.
9. Optionally configure synthetic EVT-specific HTTPS Calendar/Web sources. The public default sources are genuine holiday data unrelated to the fictional EVT dataset; their missing event IDs are correctly flagged. For an event/registration verification demo, publish your synthetic feed/reference records at public HTTPS URLs, then set `CALENDAR_FEED_URL` and `WEB_SOURCE_URL`. No URL can be supplied through the public run endpoint.
10. Only after verifying a Gemini project's free/unbilled configuration, manually set its server-side key and `GEMINI_ENABLED=true` for a controlled demonstration. Default `GEMINI_DAILY_LIMIT=10` applies in public demo mode. **Never enable it for automated regression/smoke runs.** Prior backend live generation is documented separately; no new live Gemini request was made during this work.
11. Record the actual public URLs and fresh screenshots/recordings in `docs/submission/`. An actual local screenshot set and CSV sample are present; a recording is not yet present.

## Demo access and request controls

`Continue as reviewer` creates an anonymous 24-hour demonstration token, stored in the browser tab's session storage and hashed in PostgreSQL. It is **not account authentication** or proof of identity. Public mode restricts conversation and execution objects to their creating token; prior unowned local objects are not publicly listed or accessible. Knowledge documents are deliberately synthetic and shared. Tokens travel in `X-Demo-Session`, avoiding reliance on cross-site cookies. Leaving/replacing the session removes the tab's token; it does not grant another reviewer access to old objects.

Durable PostgreSQL daily counters bound session creation (100), requests per session (2000), all public writes (100), agent runs (30) and Gemini-generation requests (10). Defaults are configurable with server-side `DEMO_*`, `AGENT_DAILY_RUN_LIMIT` and `GEMINI_DAILY_LIMIT`. At most two recent agent runs are admitted using a PostgreSQL advisory lock. Request bodies are limited to 16 KB; source reads to 512 KB, tool timeouts to 12 seconds, records to 30 per source, emails to at most 3. No automatic retry, model fallback, email send endpoint or paid infrastructure activation exists.

These controls are appropriate for a synthetic public assessment, not production identity or confidential data access. Global budgets can be exhausted by an anonymous visitor; commercial service would need genuine authentication, tenant ownership and stronger abuse protection. Database backups, retention and rotation are owner responsibilities.

## Agent execution reliability

Runs and every step transition are persisted in PostgreSQL. FastAPI BackgroundTasks executes one bounded LangGraph workflow after returning a stable run ID. It is **not a durable job queue**: if the process dies, that run does not resume. A later run-list/detail request marks executions older than ten minutes failed, retaining completed evidence and explicit interruption state. Start a fresh run rather than treating an interrupted run as successful. Free-service idle/restart behavior must be assessed on the actual host.

CSV export comes from persisted results, includes discrepancies/provenance and neutralizes spreadsheet formula prefixes. `verified_only=true` exports only genuinely verified rows; a zero-verified run produces a header-only CSV. An export step is completed only after the server generates a CSV response; the UI then initiates download. There are no fabricated completion records.

## Cold starts, cache and memory

FastEmbed is lazy and cached once per serving process. The startup indexing process downloads the model if needed; unchanged records do not re-embed. `FASTEMBED_CACHE_PATH` must be writable. A Free host's `/tmp` is ephemeral, so cold redeploys may download again. No external database or provider call is required for `/health`, but startup must complete migrations/indexing before Uvicorn serves.

Use one Uvicorn worker and one embedding thread. Installed dependencies and local fresh-database indexing are verified; **hosted cold-start latency and peak memory on the Free service remain unverified**. Do not assume a local RSS reading proves a hosted memory ceiling. If the host fails to start due to memory, capture the logs and evaluate a free-capable host with sufficient memory; do not silently upgrade to paid compute. The frontend allows bounded request waits and reports timeout without pretending the server stopped working.

## Local production-profile probe

```bash
cd backend
source .venv/bin/activate
python -m app.core.migrate
DEMO_MODE=true FRONTEND_ORIGINS=http://127.0.0.1:4173 GEMINI_ENABLED=false \
  python -m uvicorn app.main:app --host 127.0.0.1 --port 5052
```

In another terminal:

```bash
cd frontend
npm ci
npm run build
API_PROXY_TARGET=http://127.0.0.1:5052 npm run preview
TEST_BASE_URL=http://127.0.0.1:4173 PLAYWRIGHT_CHANNEL=chrome RUN_LIVE_API=true npm run test:e2e
```

Omit the Chrome channel after installing Playwright Chromium if Chrome is unavailable. Live RAG browser regression first checks `/api/demo/config` and requires generation disabled. Only Calendar/Web HTTP reads are live; Mailtrap contract and positive verification cases use clearly identified test-only adapters/fixtures.
