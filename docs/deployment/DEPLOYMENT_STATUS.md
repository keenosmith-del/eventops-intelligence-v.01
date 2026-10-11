# Deployment status — 11 October 2026

**Live; requested functional assessment workflows pass.** Implementation `428bd3522ea86f3d504ef694113de1863fc15351` was individually confirmed on both Render services after successful [CI run 38120655085](https://github.com/keenosmith-del/eventops-intelligence-v.01/actions/runs/38120655085). The final documentation follow-up retains this application implementation.

| Resource | Verified state |
| --- | --- |
| Frontend | Render Static Site, https://eventops-intelligence.onrender.com; implementation release dep-db5jf2bbc2fs738q94b0 |
| Backend | Render Free Python, https://eventops-intelligence-api.onrender.com; implementation release dep-db5jf2bbc2fs738q93ug; health/readiness pass |
| Database | Existing Neon Free production project; PostgreSQL 18.6, pgvector 0.8.6; four migrations, 19 references/embeddings, three documents, 384 dimensions; startup changed zero rows |
| GitHub | Implementation pushed to main; backend/frontend CI passed. Browser authorization/SSH available; separate gh CLI token remains invalid |

[PRODUCTION_ACCEPTANCE_REPORT.md](PRODUCTION_ACCEPTANCE_REPORT.md) records original acceptance and the superseding final results.

Real production run `ef50214e-9ec1-4903-a80c-ada28ca7d5cb`: all three tools completed; 13 parsed/normalized observations → seven saved records, one verified/six flagged, six duplicates merged. Ada's positive/duplicate messages match active P-001/EVT-101 with both message references. Lindi's inactive P-003/name conflict is flagged with field-level evidence. Five public holidays remain separately flagged. Actual browser CSVs have seven rows/all and one Ada row/verified; history restores and replay excludes downloads, including legacy exports.

Fresh production RAG returns POL-003 / 08:45. One real Gemini free-tier answer generated the correct deadline and exact retrieved citation; not_requested, unavailable and generated statuses restore distinctly. Generation is returned to disabled after the bounded test; future live generation needs explicit free-tier confirmation/enablement. Saved generated output remains inspectable in its original reviewer session.

Local regressions: 217 backend passes / one live skip; 16 frontend unit passes; build passed; 25 browser passes / three opt-in live skips. These local results are separate from real production evidence. Development database stays on 55432; tests used isolated 55433; production stays on Neon. Existing data, source credentials and local .env are preserved.

Remaining operational caveats: historical transient failure root cause not conclusively captured; current session/list probes passed, transaction/retry/error-reporting mitigations have regressions. Free-host idle wake, hosted memory headroom/soak and recovery exercises remain unverified. Optional n8n is unconfigured. No paid resource, billing activation, destructive migration or further sandbox sending occurred.
