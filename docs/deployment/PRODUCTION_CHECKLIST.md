# Production release checklist

Recorded 11 October 2026. Requested functional assessment workflows pass at implementation 428bd35; both individual service releases and CI were verified. See [actual live evidence and limitations](PRODUCTION_ACCEPTANCE_REPORT.md). Preparation items below remain historical local evidence.

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

## Provisioning — current verified state

- [x] Neon authorized; independent Free production project and pgvector confirmed.
- [x] Actual PostgreSQL 18.6 recorded (original plan/local tests used 17).
- [x] Final fixes pushed at 428bd35; current backend/frontend CI passed.
- [x] Both Render services individually live at full intended SHA; Free backend and Static Site confirmed.
- [x] Frontend public bundle embeds intended HTTPS API; actual reviewer CORS/API operation verified.
- [x] Hosted database writes match browser-generated test conversation/run IDs.
- [ ] Independent billing/spending-control audit beyond observed plans; acceptance created no resources or upgrades.

## Actual public verification

- [x] Public frontend/backend HTTPS URLs, warm health/readiness.
- [x] Neon extension/four migrations/indexes/19 embeddings/three documents/dimensions 384.
- [x] Desktop entry, real RAG/context/citation, nested restore; representative 390 px landing/entry/sources.
- [x] Cross-context conversation/run denial; public Swagger/OpenAPI disabled; trusted/untrusted CORS.
- [x] Final hosted Calendar/Web/Mailtrap execution; all three prepared email messages processed.
- [x] Processing/deduplication/missing-field checks, stored graph, CSV downloads/history match actual run.
- [x] Read-only Neon confirms saved messages, execution, five results and eleven completed stages after export.
- [x] Hosted startup and recent request logs inspected; actual application metrics unavailable on Free.
- [x] Backend redeploy persistence for conversations, old/new executions and reviewer session.
- [ ] Idle spin-down/wake-up.
- [x] Nonempty email extraction; positive verified, duplicate and inactive/conflicting live cases.
- [x] One bounded real free-tier Gemini answer, grounded POL-003 citation, saved status restoration; generation returns to disabled.
- [ ] n8n configuration/runtime/webhook handoff; currently unconfigured 503.
- [ ] Deliberate integration timeout and failed-run browser feedback.
- [ ] Full responsive workspace/results/graph breakpoint matrix.
- [ ] Hosted peak RSS/headroom and recovery exercise; do not infer from local 414 MiB measurement.
- [ ] Intentional frontend change followed by gated deploy, and deliberately failed CI preventing deploy.
- [x] Resolve generation-status restoration and post-export replay timing defects; regressions and deployed checks pass.

Do not equate configured integrations, empty Mailtrap connectivity or local fixtures with full live three-source record processing. The final pass used real deployment, one new agent run and one bounded free-tier model call to verify requested fixes; no paid upgrade or destructive operation occurred.

Final local regressions: 217 backend passes / one opt-in live skip; 16 frontend unit passes; production build passed; 25 browser passes / three live opt-in skips. Earlier preparation counts above are historical.
