# Production release checklist

Recorded 11 October 2026. Checked preparation items are local evidence, not public deployment claims.

## Preparation verified

- [x] Audit working tree; preserve prior Part 2/UI edits and v.02.
- [x] Local .env, Docker port/volume, FastAPI and npm run dev remain independent.
- [x] Exact dependencies install/pip check on Linux amd64 Python 3.12.15.
- [x] Backend: 210 passed / 1 live-Mailtrap skip.
- [x] Frontend: 12 unit tests, production build, 24 browser passes / 3 live opt-in skips.
- [x] Four migrations on disposable PostgreSQL 17/pgvector; repeat migration succeeds.
- [x] Three synthetic sources, 19 records/real embeddings, 384 dimensions; re-index zero changes.
- [x] Actual isolated RAG, contextual follow-up, POL-003 citations, restore and reviewer isolation.
- [x] Actual isolated LangGraph/Calendar/Web HTTPS, persisted results/history/CSV; Mailtrap skipped.
- [x] Backend restart preserves saved conversation/execution fingerprints and 19 embeddings; readiness 200.
- [x] Cold model load in 512 MB Linux container, peak RSS ~414 MiB; hosted memory still unverified.
- [x] Prepare GitHub Actions + Render main/checksPass, SPA rewrite, production guards.
- [x] Verify Render browser account/repository integration and GitHub SSH access.

## Provisioning — outstanding

- [ ] Approve pending Neon Console GitHub OAuth (read-only email addresses); complete any signup terms yourself.
- [ ] Actual Neon Free independent production project/database, PostgreSQL 17, pgvector/TLS and quotas verified.
- [ ] No trial, payment information, paid upgrade or automatic billing introduced.
- [ ] Review/commit/push the complete required v.01 implementation and deployment preparation; remote CI passes.
- [ ] Review Render Free/backend/static-site and workspace spending controls before provisioning.
- [ ] DATABASE_URL supplied securely only to Render; exact API/frontend origins set.
- [ ] Optional dedicated Mailtrap/Gemini settings on backend only; generation disabled for checks.
- [ ] Connected repo/main, whole-repo root and After CI Checks Pass confirmed on both services.
- [ ] Deploy and compare actual release SHA with passed CI SHA.

## Actual public verification — outstanding

- [ ] Public frontend/backend HTTPS URLs recorded after testing.
- [ ] Health/readiness pass, including cold idle start.
- [ ] Neon extension, four migrations/indexes, 19 records/embeddings, three documents, dimensions 384.
- [ ] Landing/mascots/reviewer entry, all five views/nested refreshes, no JS/CORS errors.
- [ ] Real RAG/evidence/citation rendering, contextual follow-up and fresh-page restore.
- [ ] Cross-session conversation/run access denied; public docs/debug disabled.
- [ ] Hosted Calendar/Web remote steps succeed; Mailtrap actual remote call separately verified if configured.
- [ ] Processing/deduplication/discrepancies, graph statuses, saved verification, CSV/history match actual run.
- [ ] Same reviewer conversation/run retains evidence/results after restart/redeploy.
- [ ] Unchanged sources do not duplicate/re-embed unnecessarily.
- [ ] Intentional frontend commit → passing CI → changed hosted frontend and matching SHA.
- [ ] Failed required CI demonstrated to prevent automatic deployment.
- [ ] Hosted logs/memory/quotas checked, credentials private, actual backup/recovery options inspected.

n8n runtime/cloud execution is optional and unverified. Do not mark connected based on the export. Do not substitute synthetic EVT fixtures for actual external observations. Never use live Gemini generation as an automated deployment test.
