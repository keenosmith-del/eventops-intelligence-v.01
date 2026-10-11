# Production acceptance — 11 October 2026

**Production status: Partial Pass.** The deployed reviewer journey, retrieval, real LangGraph tool reads, persisted results, CSV downloads and history work. Full assessment completion is not established: Mailtrap is empty, no live positive verification/conflict case was produced, Gemini generation was not requested, and n8n is unconfigured. Hosted memory headroom and idle wake-up remain unmeasured. Two reproducible behavior defects are recorded below; no implementation or provider configuration was changed to pass checks.

Test window: approximately 08:25–08:44 Africa/Johannesburg (UTC+2). Evidence was obtained through actual Chrome and an independent Codex in-app Chromium context, public HTTP requests, signed-in Render/GitHub dashboards and read-only Neon SQL. Provider browser authorization was available; the separate gh CLI token is invalid. No keys, tokens or database URLs were printed. Only acceptance conversations, one bounded execution and its exports were created. No reset, deletion, migration execution, restart, deployment, paid resource, model generation, commit or push was performed.

## Deployment and revision

- Frontend: https://eventops-intelligence.onrender.com
- Backend: https://eventops-intelligence-api.onrender.com
- Repository: https://github.com/keenosmith-del/eventops-intelligence-v.01
- Both services and local HEAD: `6128bd1c8ba250fdc1213011ca753ea598077a7a`.
- [GitHub Actions run 38117990875](https://github.com/keenosmith-del/eventops-intelligence-v.01/actions/runs/38117990875): successful, 59 seconds. Backend job succeeded in 56 seconds; frontend in 55 seconds. CI is regression evidence, not a substitute for the live checks below.

| Service | Render service | Individually confirmed live deployment | Duration |
| --- | --- | --- | --- |
| Backend | srv-db5ikgg473hc73babptg, Free Python, Oregon | dep-db5ingng0jfs73bee6dg, Blueprint, full SHA above | 1m38s |
| Frontend | srv-db5ikgg473hc73babpu0, Static Site | dep-db5ingn79l7c73fluui0, Blueprint, full SHA above | 19.7s |

Both also had same-SHA automatic deployments immediately beforehand: backend `dep-db5ing0ae00c739nspr0` (1m52s), frontend `dep-db5ing0ae00c739nsq70` (20.5s). This is duplicate deployment activity, not a revision mismatch. Blueprint sync alone was not used as proof. Frontend build used Node 24.21.0 and `bash scripts/build-frontend.sh`; published JS contains the intended public API origin and no `localhost:5050`. Build succeeded with a nonfatal roughly 505 KB JS chunk warning. CI emitted action runtime/runner migration warnings, without failed jobs.

Backend startup logs show release SHA, unchanged indexing (19 validated, zero changed/pending), model download, application startup complete and binding to port 10000. The new service was live at 08:28:35. An older process shut down during the overlapping rollout; this is observed deployment replacement, not evidence of an OOM crash. HF unauthenticated-download warning was nonfatal. Root GET/HEAD 404 is expected; readiness and liveness have their own routes.

## Hosted database proof

Neon Free project `eventops-intelligence-v01` (`small-surf-91232747`), default production branch `br-twilight-snow-b4igm2pv`, database `neondb`, AWS Ohio. Actual PostgreSQL **18.6 (c021049)** differs from the original PostgreSQL 17 provisioning plan. This acceptance did not change it. pgvector **0.8.6** is installed and compatible with the tested operations.

Read-only transactions in the signed-in SQL editor confirmed:

- `001_knowledge_records.sql`, `002_rag_conversations.sql`, `003_agent_runs_and_demo.sql`, `004_n8n_triggers.sql` in schema_migrations.
- 19 knowledge rows, 19 embeddings, three distinct documents, vector dimensions `{384}`.
- Knowledge indexes: primary key, idx_knowledge_event, idx_knowledge_record_type, idx_knowledge_metadata. No approximate vector index was observed; the small corpus retrieves successfully.
- Four saved messages for browser conversation `f34e97c5-00c3-4341-b272-08f4d9bbff61`.
- Browser run `0920399b-9951-44b9-8d67-7fff3f1ba043`: completed; five JSON result records; summary total 5, flagged 5, verified 0, duplicates merged 5; all tool outcomes completed; mode `real_https_read_only`.
- Eleven saved stages, all completed after the requested exports. Ten processing stages settled before export. Actual created/finished timestamps: 06:32:28.936688Z / 06:32:41.406868Z.

Matching browser-generated IDs in this hosted project prove that the API writes to Neon, rather than merely reading a local seed. Fresh page loads and a fresh HTTP connection restore data. Persistence across an intentional backend restart/redeploy was **not tested**. A new anonymous reviewer correctly cannot retrieve another reviewer's saved records; a fresh connection retaining the original reviewer identity can.

Neon overview showed six-hour recovery retention and Free compute range 0.25–2 CU. Actual restore/recovery was not attempted.

## Real reviewer journey

| Check | Outcome and evidence scope |
| --- | --- |
| Landing → Start → reviewer entry → workspace | Production browser: passed in Chrome and independent Chromium context; genuine API sessions, not fixtures |
| Images/styles/fonts | Production browser: mascot assets loaded, styled desktop layout; computed body font Inter/system stack. Screenshots inspected. No broken image observed |
| Responsive | Production browser: 390×844 landing, reviewer entry and sources; no document overflow at 390 px; mobile navigation replaces sidebar. Full mobile agent/result table interaction and other breakpoints not exhaustively tested |
| Supported nested routes | Production browser: conversation, verification and history direct navigation/refresh work under existing session |
| Knowledge question | Exact requested question retrieved POL-003, score 0.862, 08:45 South Africa Standard Time, citation data/structured/policies.csv#policy_id=POL-003 |
| Contextual follow-up | “What time does its check-in close?” retained EVT-101; POL-003 score 0.860; original question/evidence retained |
| Restore | Production browser: both exchanges survived refresh; Neon independently confirmed four messages |
| Generative answers | Not tested. Request Gemini answer was unchecked; browser explicitly showed evidence-only / generation not requested. No live model call was authorized or executed. Actual provider enablement flag was not inspected; this is retrieval-only evidence, not a claim that Gemini is enabled or disabled |
| Knowledge Sources | Production browser + Neon: directory.json 7, events.csv 3, policies.csv 9; all indexed. POL-003 expands to its real policy/reference. Uploads explicitly unavailable; no decorative upload was substituted |

### One actual agent execution

Reference EVT-101, maximum five records per source. Starting feedback/disabled controls were observed, followed by completed outcome. Intermediate real-time running states were not captured before the roughly 13-second run finished. Saved stage timestamps and replay running/pending states were inspected; those are historical evidence, not an additional execution.

| Integration | Real outcome | Limit |
| --- | --- | --- |
| Calendar / OfficeHolidays HTTPS ICS | Completed, five parsed observations; saved timing 08:32:31–32 | Public holidays, not fictional EVT registrations |
| Web / Nager ZA holidays 2026 HTTPS API | Completed, five observations; saved timing 08:32:34–35 | Public reference observations, no matching EVT ID |
| Email / Mailtrap read-only sandbox | Completed actual read; zero messages; 08:32:32–33 | Connectivity proved; nonempty email extraction and three-source record processing unproved |
| n8n | Public service status GET returned 503; implementation's unconfigured-service response | Runtime/webhook/import/idempotent handoff not verified; no trigger was sent |

LangGraph persisted extraction 10, normalization 10, deduplication 5, verification/flagging 5 and PostgreSQL persistence 5. Actual stage timestamps progress sequentially through all ten processing stages. The graph shows branching data flow and explicitly says tool reads are sequential. No fixture fallback or fabricated verified claim was observed.

## Verification, exports and history

Five saved public-holiday records: New Year's Day, Human Rights Day, Good Friday, Family Day, Freedom Day. All correctly show review required / missing details / missing_event_id. Calendar and web each contribute evidence to five merged records; five duplicates were merged. No conflicting-value or positive verified production case occurred, so those rendering paths remain unproven live.

Inspect record opened normalized fields, both raw source values, original evidence/URLs, field-level failed event-reference check and the explanation that no authoritative reference matched. Verified filter yielded no rows; restoring All records yielded five. Calendar/source and missing-event-ID discrepancy filters retained the expected five. Not every combination was exercised.

Actual browser export controls downloaded all-record CSV (five rows, 12 columns) and verified-only CSV (header, zero rows). Parsed row count, all five titles and review_required statuses match the visible table and Neon's persisted five-result summary. CSV files stayed in the browser's Downloads directory, outside the repository/development database; no production dataset was imported locally. The browser automation download event timed out even though Chrome downloaded the file; filesystem inspection confirmed the actual artifact. This is an automation observation limitation, not an export failure. Exported evidence fields were present; a byte-for-byte comparison of every field against SQL was not performed.

History listed the completed run, reopened its graph/stages/results, and restored after refresh/direct navigation. Replay visibly reconstructs pending/running nodes from saved timestamps and states that no tools are called. Pause/return-to-complete controls worked.

## Security, errors and reliability

- Production API: health/readiness 200; measured warm probes about 0.38s / 1.51s. Exact trusted frontend CORS allowed; untrusted origin preflight 400 without allow-origin. Public /docs and /openapi.json returned 404.
- Missing session: protected conversations/run access 401. Different valid reviewer: conversation and run 404. Malformed run UUID: 422. No stack trace in sampled errors.
- Independent Chrome and in-app Chromium sessions: second context saw no conversations/executions, “Execution not found in this demonstration session” and “Conversation not found” for first-reviewer IDs. An initial cross-run view also said saved executions unavailable; later own history loaded correctly empty. No cross-reviewer record was revealed. The temporary list-error cause was not established.
- Captured warn/error console logs were empty in both reviewer tabs. Render request logs corroborated live reads/writes, CORS preflights, requested exports, expected authorization/validation statuses and explicit n8n 503. No broad HAR/network trace was captured; absence of every possible failed request is not claimed.
- Existing safe smoke script was read and run with --api / --frontend, **without --agent** (one browser run only). First network-authorized attempt passed health/readiness/CORS/session-required then stopped at session creation around 08:28:35 rollout. Exact response/cause not captured. Deployment overlap is a plausible inference, not confirmed root cause. One controlled rerun passed all default checks, including contextual RAG, source citation, fresh-connection restoration and reviewer denial; smoke conversation b6a03c63-0519-4e78-b289-2aca9721a194. Initial sandbox connection failures are local tool-network restrictions, not service failures.
- Render startup: script 08:27:47; indexing done 08:28:05; Uvicorn startup 08:28:24; model files downloaded approximately 08:28:25–29; app ready 08:28:31; live 08:28:35. Deployment model cold load succeeded. Inactivity spin-down/wake-up was not deliberately forced; dashboard warns 50s or more.
- Render Free memory limit is 512 MB, but CPU/RSS metrics are gated behind paid upgrade. **Hosted memory within limit cannot be quantified.** Prior isolated Linux peak ~414 MiB is local evidence only. No OOM, tool timeout, unexpected traceback or new crash appeared in inspected startup/recent request windows. This does not guarantee headroom or long-term stability. No stress test, paid upgrade or repeated execution was used.
- Successful startup, source access, retrieval and Mailtrap run demonstrate the required settings for those paths function. Secret values and all environment flags were not inspected. No blanket “all environment variables correct” claim.

## Confirmed defects versus demonstration gaps

1. **Functional defect: historical generation status is not persisted.** After refresh, an evidence-only exchange changes to “No AI answer stored. The generation outcome for this historical exchange was not persisted by the API.” Evidence survives, but the original “not requested” status is lost. Persist/restore outcome without invoking Gemini.
2. **Functional defect: export timing extends execution replay.** The run ended 08:32:41; verified export later wrote the export stage at 08:39:27. Replay then spans 417.16 recorded seconds, including the idle interval. The export stage also reflects the latest verified-only zero-row export after a prior all-row export. Keep run timing and subsequent download audit events distinct, or bound processing replay to run completion. No production fix applied.
3. **Observed intermittent entry/list failures:** first smoke session creation failed during overlapping deploy; a second-browser cross-run list briefly failed and later recovered. These are unresolved observations, not proven systemic defects or identified error codes. Record safe status/timing telemetry and retest outside rollout/after idle wake.
4. **Assessment gaps:** nonempty Mailtrap processing; positive verified/conflicting/inactive cases with genuinely connected, explicitly labelled synthetic source data; live Gemini if required and separately authorized; configured/executed n8n if required; idle wake/redeploy persistence and hosted memory measurement; deliberate integration timeout/failed-run UI. Do not mark these passed from local fixtures.
5. **Scope limitation:** document upload is unimplemented and clearly disclosed. No file was uploaded during acceptance.

## Five priorities before final demonstration

| Priority | Category | Proposed later change / acceptance condition |
| --- | --- | --- |
| 1 | Demonstration coverage | Arrange a dedicated nonempty synthetic Mailtrap sandbox and connected EVT-compatible observations; obtain at least one verified record, duplicate and conflict with traceable evidence. Preserve live/public observations as such; never silently replace them with fixtures |
| 2 | Functional | Fix export/replay timing and historical generation outcome persistence; refresh must preserve evidence-only reason and replay must avoid post-run idle time |
| 3 | UX recommendation | Add a short reviewer sequence and concrete expected outcomes linking Knowledge Assistant → Agent Workspace → Results → History. Explain that RAG and verification share references but RAG questions do not start runs; identify what each source adds |
| 4 | Reliability | Investigate duplicate same-SHA auto/Blueprint rollouts and transient reviewer entry; expose useful safe waiting/retry feedback, capture status/timing, and verify idle wake, redeploy persistence and memory without excessive load |
| 5 | Assessment/integration | Explicitly decide whether live grounded Gemini and n8n are required; perform individually authorized bounded tests/configuration if so, otherwise label them optional/unverified in the demonstration |

Further UX recommendations (subjective, no redesign performed): explain “completed” versus “verified” and empty Mailtrap separately; distinguish missing details from conflicts; clarify source counts count merged evidence twice; explain all-record export is independent of filters and empty verified export; distinguish replay from starting a new execution. Start/examples/navigation already provide a usable entry; the main confusion is purpose and transitions among four similar workflow views. Desktop low-contrast explanatory copy is readable but small; assess contrast/readability separately before changing the approved design.

## Evidence and safe demonstration path

Screenshots are real production states in ../submission/screenshots/: production-landing-desktop.jpg, production-landing-mobile.jpg, production-reviewer-entry.jpg, production-entry-mobile.jpg, production-rag-policy-evidence.jpg, production-rag-contextual-followup.jpg, production-agent-completed.jpg, production-record-evidence.jpg, production-history-replay.jpg, production-history-restored.jpg, production-knowledge-sources.jpg, production-sources-mobile.jpg, production-reviewer-isolation.jpg, production-neon-migrations-vectors.jpg, production-neon-persisted-run.jpg. Provider screenshots avoid credentials. Desktop/mobile representative screenshots were visually inspected; screenshots are evidence snapshots, not assertions that every breakpoint/path was tested.

For the present reviewer demonstration: Start → Enter workspace → exact EVT-101 policy question → contextual follow-up → evidence/citation → Agent Workspace (explain holiday sources first) → one bounded run only if needed → inspect flagged merged evidence → export → saved history/replay → Sources. The current saved acceptance run is retained in its reviewer Chrome tab. Anonymous reviewer sessions are scoped and expire; share the public entry URL, not a private session token or an expectation that other reviewers can open this run.

Existing local regression results remain historical (210 backend passes/1 skip, 12 frontend unit passes, 24 production-preview browser passes/3 live skips). No new local regression suite was needed for documentation-only changes; successful current CI is separately verified. None of those results proves a live skipped integration. No deployment provisioning blocker remains; the remaining blockers are full demonstration coverage and the explicitly unverified reliability/integration requirements above.

## Final assessment improvement pass — in progress

The findings above describe the original acceptance revision, not the final improvements. Targeted fixes now remove CSV downloads from execution timing, persist generation outcomes for restored exchanges, separate list-loading errors from run-detail errors, allow bounded unavailable-read recovery, and admit reviewer sessions atomically. Short reviewer guidance preserves the existing visual language.

Local validation: 217 backend tests passed, one opt-in live integration test skipped; isolated disposable PostgreSQL on port 55433, separate from development on 55432 and Neon. Frontend validation and production deployment verification are pending in this pass.

The owner submitted the three prepared synthetic registration messages through sandbox SMTP, once each. Actual Mailtrap API read confirmed IDs 5748068714 (positive), 5748076082 (duplicate), and 5748076401 (inactive-conflict). This proves retrieval; production LangGraph outcomes remain pending until the new revision is deployed. No further submission is required.
