# Deployment status — 11 October 2026

**Blocked: prepared and locally verified; public hosting has not been provisioned.**

| Resource | Provider | Actual state / verified URL |
| --- | --- | --- |
| Frontend | Render Static Site (planned) | No EventOps service created; no public URL verified |
| Backend | Render Free Python (planned) | No EventOps service created; no public health check possible |
| Database | Neon Free PostgreSQL/pgvector (planned) | No project/database created; Neon OAuth approval pending |
| GitHub | keenosmith-del/eventops-intelligence-v.01/main | SSH read access verified; gh token invalid; no commit/push |

Render's existing GitHub sign-in succeeded without a new grant. Its v.01 Blueprint draft parsed the existing committed YAML, but **Deploy Blueprint was not submitted**. Local YAML changes are not on GitHub and no production database URL is available. Neon reached **Authorize Neon Console** for read-only email addresses; this new grant was left for the owner. Complete any account terms yourself. Never paste secrets into chat. No paid resources, billing changes, purchases or new Gemini calls occurred.

## Verification evidence

| Check | Result / scope |
| --- | --- |
| Working tree | Prior UI/Part 2 edits retained; v.02 untouched |
| Linux dependencies | Locked install and pip check passed, Linux amd64 Python 3.12.15 |
| Backend | 210 passed / 1 live-Mailtrap skip on host and Linux |
| Frontend unit/build | 12 passed; build passed, existing ~505 KB non-fatal JS warning |
| Browser | Production preview: 24 passed / 3 live skips in 15.0 s. Dev replay counted two StrictMode reads; deployment CI uses production build without product changes |
| Database | Disposable PostgreSQL 17/pgvector, port 55433; all four migrations; 19 real 384-dimensional embeddings across three sources; repeat indexing unchanged |
| RAG | Real HTTP isolated backend port 5058: POL-003 citation/retrieval, contextual follow-up, persisted restore and second-reviewer denial |
| Agent | Actual LangGraph, successful Calendar/Web remote HTTPS; Email intentionally skipped; persisted outcomes/results/history and CSV row counts passed |
| Mailtrap | Not called by this task; hosted sandbox remains to configure/verify. Earlier local empty-inbox evidence is separate |
| Gemini | Disabled throughout indexing/tests/smoke; no new live generation |
| Restart | Actual deployment start script restarted isolated backend; conversation/run fingerprints unchanged; 19 embeddings retained, zero indexing changes, readiness 200 |
| Model/memory | Clean 512 MB Linux container, cold download ~18 s, app import, document shape (19,384), query (384,), peak RSS 423,636 KiB (~414 MiB) |
| Public health/RAG/agent | Not run: no public resources/URLs |
| Hosted cold start/redeploy | Unverified; local/container evidence does not prove hosting behavior |
| Auto-deploy | Workflow/main/checksPass prepared, not committed/activated/verified remotely |
| n8n | Inactive protected workflow preserved; runtime import/webhook/cloud execution unverified; LangGraph independent |

The first sandboxed tests could not access sockets. Authorized checks then used only an isolated database. Its fresh reference dataset was seeded before the final passing agent regression. These setup issues were resolved; development data was not the test target.

The 512 MB model test is promising but actual hosted overhead/concurrency/cold-start behavior still needs observation. BackgroundTasks cannot resume interrupted runs. Free quotas/backup recovery require account inspection. No model replacement, dimension/schema change or paid upgrade occurred.

## Exact remaining actions

1. Approve **Neon Console → read-only email addresses** in the pending GitHub authorization tab, and complete any signup terms. Create/select a strictly Free independent production project and supply its TLS URL only to Render's secure backend environment.
2. Intentionally commit/push the reviewed complete required v.01 implementation/deployment changes to main. Git SSH works; gh reauthentication is needed only for its API features.
3. Complete the Render Blueprint with actual origins/database, verify Free settings and approve final public provisioning if computer-use policy requires it. Execute the [public release checklist](PRODUCTION_CHECKLIST.md).

## Files changed by deployment preparation

Created: `.github/workflows/ci.yml`, `backend/app/core/environment.py`, `backend/tests/test_deployment.py`, `scripts/build-frontend.sh`, `scripts/smoke-production.py`, `docs/deployment/PRODUCTION_CHECKLIST.md`, `docs/deployment/DEPLOYMENT_STATUS.md`.

Modified: `render.yaml`, `scripts/start-backend.sh`, `backend/app/core/database.py`, `backend/app/main.py`, `backend/app/api/rag.py`, `backend/app/rag/embeddings.py`, `backend/app/rag/generation.py`, `frontend/playwright.config.js`, `docs/deployment/README.md`, root `README.md`.

Other existing modified/untracked UI, Part 2, test, docs and screenshot files were retained. This task did not change .env, Compose, SQL migrations, Vite dev/proxy, frontend product files or dependency pins. Tests used disposable infrastructure/auxiliary ports, removed after verification. All changes remain uncommitted/unpushed; no public deployment is claimed.
