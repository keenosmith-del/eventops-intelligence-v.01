# Deployment status — 11 October 2026

**Live; production acceptance Partial Pass.** Neon authorization and provisioning are complete. Both Render services individually show live revision `6128bd1c8ba250fdc1213011ca753ea598077a7a`, matching successful GitHub Actions run 38117990875.

| Resource | Actual verified state |
| --- | --- |
| Frontend | Render Static Site, https://eventops-intelligence.onrender.com; deploy dep-db5ingn79l7c73fluui0 |
| Backend | Render Free Python, https://eventops-intelligence-api.onrender.com; deploy dep-db5ingng0jfs73bee6dg; health/readiness pass |
| Database | Neon Free eventops-intelligence-v01, production branch; PostgreSQL 18.6, pgvector 0.8.6; four migrations, 19 records/embeddings, three documents, 384 dimensions |
| GitHub | main at 6128bd1; backend/frontend CI succeeded. Browser access available; separate gh CLI token invalid |

See [PRODUCTION_ACCEPTANCE_REPORT.md](PRODUCTION_ACCEPTANCE_REPORT.md) for exact live tests, revisions, database proof, integration outcomes, screenshots, defects and limitations. Earlier “blocked at Neon authorization / no public hosting” statements are superseded by this acceptance.

## Confirmed production behavior

Real browser reviewer entry, POL-003 retrieval (08:45 SAST), contextual follow-up and restore passed. One bounded real LangGraph run persisted five flagged records from five Calendar and five Web observations, merging five duplicates. Mailtrap completed its actual HTTPS read but returned zero messages. Record evidence, field-level checks, filters, five-row/all and zero-row/verified CSV downloads, saved history and timestamp replay were inspected. Independent reviewer contexts cannot access one another's resources. Public docs/debug routes are unavailable; exact frontend CORS is enforced.

## Remaining work

- Nonempty controlled Mailtrap extraction and positive/conflicting verification cases remain unproved live; public holidays do not match fictional EVT IDs.
- No live Gemini generation was requested; retrieval-only is proved. n8n public service status returns 503/unconfigured; no webhook execution was attempted.
- Fix historical generation outcome restoration and export-induced replay idle time in a later authorized implementation pass.
- Investigate initial transient session/list failures. Overlapping same-SHA automatic/Blueprint deployments were observed; causal attribution remains unconfirmed.
- Render Free's 512 MB RSS metrics require a paid plan, so actual memory headroom is unmeasured. Startup/model load succeeded with no observed OOM in inspected windows. Idle wake, restart/redeploy persistence and deliberate timeout/failure paths remain untested.
- Add clearer reviewer guidance linking retrieval, agent verification, saved results and history without changing the approved design during acceptance.

The earlier local Linux tests (210 backend passes/1 skip; 12 frontend unit passes; 24 production-preview browser passes/3 skips; ~414 MiB local peak RSS) remain historical local evidence, not proof of hosted skipped paths. This pass changed only documentation and screenshots. No commit/push, production configuration change, paid resource, model call or destructive database operation occurred.
