# Part 2 — execution, progress and results

Local assessment audit, 10 October 2026. No deployment, paid model calls, automatic commits or pushes. Approved Introduction/sign-in styles and KnowledgeAssistant source are unchanged. Public frontend preview uses port 4173 and an isolated Gemini-disabled backend on 5052; normal development remains 5173 → 5050 with exact-origin CORS.

## Capability and evidence

| Capability | Implemented | Verification / limits |
| --- | --- | --- |
| Start and observe a real execution | Existing bounded POST and immediate detail polling, 350 ms while active | Real HTTPS/PostgreSQL browser journey; gated backend stage test observes actual persisted running/completed/pending transitions |
| Visible progress | Distinct statuses, only active stage/edges animate, real counts, automatic selection and manual override | Browser polling test changes API snapshots under explicit test control; production has no timed fake stages; reduced motion disables animation |
| Recorded replay | Actual saved timestamps, pause/resume/speed/seek/return, explicit recorded mode | Pure timestamp tests plus browser replay test verifies no extra run-detail request or new execution; missing timestamp stages cannot be reconstructed |
| Graph clarity | Separate Calendar/Email/Web branches converge to extraction | Branches depict data flow; actual backend tool reads remain sequential. Measurement preservation fixes running-canvas blankness; desktop/mobile nodes are visible |
| Saved verification results | Raw/normalized values, comparison decisions, authoritative fields, evidence, missing/conflict analysis | Live record inspection and PostgreSQL synthetic assessment test. Old runs without additive fields show “not recorded” |
| CSV downloads | All and verified-only exports from actual stored results | Browser compares downloaded bytes with real endpoint text (ignoring only UTF-8 BOM); controlled backend test parses rows/IDs/statuses; verified-only live export is header-only |
| Execution history | Reviewer-owned saved runs restore graph, statuses/results and export stage | Actual browser navigation, reload and persisted history recovery; service-created runs do not appear in public reviewer history |
| Knowledge Sources | Backend counts/types/indexing/content/provenance | Actual 19-record source view and explicit mocked transport assertions; no upload action |
| Sidebar tooltips | One active tooltip, pointer leave/click/outside click/navigation/Escape/window blur dismissal | Browser tests cover hover switching, click targets, ordinary focus dismissal and keyboard focus |
| Calendar/Web | Bounded real HTTPS reads | Actual public records retrieved/parsed/persisted; they do not become fictional EVT registrations |
| Mailtrap | Actual configured HTTPS list/body adapter, separate empty/failure outcomes | Connected sandbox remains empty. Opt-in two-GET probe skips without creating a run; no live email-body processing claim |
| n8n | Protected FastAPI trigger/status, idempotent delivery ledger, inactive workflow JSON | PostgreSQL-backed API tests verify auth/isolation/concurrent delivery/persistence. No n8n executable/container/runtime execution available; import/webhook validation remains pending |

## Actual request audit

Initial live run `950d45f1-b797-413a-ba15-f77cc4e00631`:

- `POST /api/agents/runs`, body `{"event_id":"EVT-101","max_records":10}` → **202**, returned pending run UUID. A valid reviewer header was used; its value is deliberately omitted.
- `GET /api/agents/runs/{id}` → **200** across actual calendar-running, email-running, web-running, transformation and persistence snapshots. Terminal outcome: completed, 12 records, 12 flagged, 0 verified, 8 duplicates merged.
- `GET /api/agents/runs/{id}/results`, both `/export.csv?verified_only=false` and `true`, `GET /api/agents/runs`, and `GET /api/knowledge/sources` → **200**. Verified-only CSV contained no data rows.

Inspected browser execution `2af07aa4-a720-4012-94ac-e624904220cc` used the default maximum of 20. Persisted mode: `real_https_read_only`; all three tool reads completed, **Mailtrap messages read: 0**. Extraction: **27** (Calendar **14**, Web **13**, Email **0**); normalization **27**; deduplicated **16**; **0 verified / 16 flagged / 11 merged duplicates**. These public holiday observations lack EVT IDs and remain flagged. “Completed” records tool/workflow completion, not verified registration validity.

Retained controlled assessment `3e6dd775-e026-46f7-8072-c3c67627fb01` has mode `controlled_assessment_fixture`: synthetic Calendar **1**, Email **3**, Web **2**, **6 extracted/normalized → 5 results**, **2 verified / 3 flagged / 1 merged duplicate**. It persists real PostgreSQL/API/CSV outcomes against actual indexed references. It includes inactive/name-mismatch, missing-event and unknown-participant cases. Source inputs are explicitly synthetic; no production adapter falls back to these fixtures. The creating reviewer session owns it; UUID alone cannot grant access to another public session. Reproduce with the test below rather than sharing session credentials.

## Failures and root causes

| Route/action | Observed request/response or UI failure | Root cause and resolution |
| --- | --- | --- |
| `/agents/runs/{id}` during polling | Detail **200**, running graph became blank; measured nodes stayed `visibility:hidden` and edges vanished | Rebuilt controlled node objects discarded React Flow dimensions on each poll. Preserve measurements through `useNodesState`/`onNodesChange`; fit after node initialization and support mobile scale |
| Terminal run polling | Potential terminal run with persistence stage not completed | Separate commits allowed a polling race. Terminal status/results and persistence completion now share one transaction; regression test verifies the observable final state |
| All collapsed sidebar routes | Hover CSS also matched ordinary `:focus`; click left a tooltip visible alongside another | Explicit single tooltip state and global dismissal replace focus/hover-only CSS. Keyboard focus remains supported |
| `/history` browser selector | No failed HTTP response; strict selector matched sidebar “Execution history” and “Open execution history” | New view link made the old substring test ambiguous; test uses exact accessible name |
| CSV content assertion | Export **200**, browser text decoding removed BOM while downloaded file retained it | Compare content after removing only leading BOM; result content and identifiers remain checked |
| RAG follow-up | `POST /api/conversations/{id}/messages`, `generate_answer:true` → **429**, `{"detail":"The demonstration request budget has been reached. Try again tomorrow."}` | Today's configured generation-request quota was exhausted. Kept the quota unchanged. Browser verifies visible budget error, retries the same follow-up with generation false → **200 / not_requested**, restores original wording and POL-003 source citation. Earlier check returned unavailable with generation disabled |
| Tooltip navigation test | Fixture reviewer token reached unmocked Agent endpoint → actual **401**, session exited | Test isolation error, not tooltip behavior. Stub the Agent reads for that fixture; live routes remain tested independently with actual sessions |
| First backend test invocation | Local database connection errors within sandbox | Restricted localhost networking. Reran unchanged suite with authorized local-network access; no DB/auth configuration weakened |
| Mailtrap controlled-message test | Real successful inbox list with **zero messages** → explicit skip | No message to retrieve; no run or fabricated evidence created. Connection failures fail rather than skip |
| n8n execution | No executable/runtime/container present | Prepared inactive workflow and setup instructions; runtime execution remains unverified |

## Reproduction and results

From `backend/` (configured local PostgreSQL required):

```bash
GEMINI_ENABLED=false .venv/bin/python -m pytest -q --tb=no
# Explicit synthetic assessment using real persistence; retained only when requested:
RETAIN_CONTROLLED_ASSESSMENT=true GEMINI_ENABLED=false .venv/bin/python -m pytest \
  tests/test_part2_execution.py::test_controlled_assessment_persist_inspect_export_and_restore -q -s --tb=no
# Single bounded real Mailtrap scenario, never sends mail:
RUN_MAILTRAP_LIVE=true GEMINI_ENABLED=false .venv/bin/python -m pytest \
  tests/test_mailtrap_live.py -q -s -rs --tb=no
```

- Complete backend: **198 passed, 1 skipped in 1.95 s**. Seven new Part 2 tests cover persisted transitions/atomic completion, actual comparison values, service auth/idempotency/isolation, absent configuration, concurrent delivery, workflow structure and controlled assessment persistence/export/history. Service test budgets use isolated real PostgreSQL buckets and remove them afterwards.
- Explicit retained synthetic assessment: **1 passed in 0.59 s**; recorded UUID above.
- Opted-in Mailtrap probe: **1 skipped in 0.56 s**, “Mailtrap connected; inbox empty. Insert the controlled test email.” Connection/body failures remain errors.
- Frontend unit tests: **12 passed**, 2 files, in 78 ms (8 API client + 4 execution helpers).
- Production build: **passed**, 2,106 modules, 0.93 s. JS 504.68 kB / 161.72 kB gzip, CSS 62.72 kB / 12.60 kB gzip. Vite emits its existing single-bundle size advisory; build succeeds.
- Complete Chrome browser suite: **25 passed in 24.2 s**, all live opt-ins enabled. Final live agent UUID `0db218eb-2f67-4349-9ef2-e2bb32e952df`; restored RAG UUID `3f34f27a-efff-402f-b77c-201319f2ba48` preserved four messages and POL-003 retrieval citation, with zero generated answers. Explicit test fixtures exercise UI state; the opted-in journeys independently exercise real backend/HTTPS/PostgreSQL persistence. No Gemini-generated answer is fabricated; no live model request is made.

From `frontend/`, after starting the isolated backend with `GEMINI_ENABLED=false`:

```bash
npm run build
npm test
API_PROXY_TARGET=http://127.0.0.1:5052 npm run preview
TEST_BASE_URL=http://127.0.0.1:4173 PLAYWRIGHT_CHANNEL=chrome \
  RUN_LIVE_API=true RUN_LIVE_ENTRY=true npm run test:e2e
```

Actual desktop/mobile graph, agent, results, sources and restored-history screenshots are `docs/submission/workspace-redesign/part2-*.png`. They show real public observations and zero email messages. No recording or public deployment URL exists.

## Files and remaining actions

Part 2 implementation includes `frontend/src/execution.js`, `components/ExecutionReplay.jsx`, `components/AgentWorkspace.jsx`, workspace CSS; backend workflow/repository atomic persistence, verification checks, protected n8n API/main middleware, migration 004, `.env.example`, and inactive n8n JSON. Some of these were already saved in the local n8n checkpoint during the work; this pass preserves that checkpoint.

Current review files relative to the preserved local n8n checkpoint:

- `frontend/src/components/AgentWorkspace.jsx`, `ExecutionReplay.jsx`, `WorkspaceSidebar.jsx`, `frontend/src/workspace-redesign.css`.
- `frontend/tests/browser/agent.spec.js`, `workspace.spec.js`.
- `backend/app/agents/workflow.py`, `backend/tests/test_mailtrap_live.py`, new `backend/tests/test_part2_execution.py`.
- `README.md`, `frontend/README.md`, `backend/README.md`, `backend/app/agents/README.md`, `automations/README.md`, new `automations/n8n/README.md`, new `docs/testing/PART2_EXECUTION.md`.
- Eight new `docs/submission/workspace-redesign/part2-*.png` screenshots: agent/graph/history desktop and mobile, results desktop, sources desktop.

These edits add/fix execution-mode provenance, measured-node stability, replay-step memoization, sidebar dismissal, test coverage, Mailtrap probe labeling and review documentation. Approved entry components/styles and KnowledgeAssistant are unchanged. No automatic commit or push was performed.

1. Insert the documented [controlled Mailtrap message](MAILTRAP_INTEGRATION.md), then run the single bounded live probe above. Until it passes, email-body retrieval/extraction/persistence is pending.
2. Configure/import/test the [protected n8n handoff](../../automations/n8n/README.md), recording an actual webhook execution/run ID and idempotent retry. Do not show a connected UI status before this evidence exists.
3. Review local changes. Deploy only through the existing deployment instructions with server credentials and exact trusted origins; hosted persistence/cold-start verification and a real recording remain owner actions.

No document-upload or unrelated redesign work is included. FastAPI BackgroundTasks remains non-resumable; replay cannot reconstruct missing historical timestamps or every repeated export because the backend stores the latest export step.

Subsequent user-authorized UI refinements replace the entry/app footer with a shared one-line copyright component and add assistant examples, collapsed-only tooltip behavior, outside-click Settings dismissal, mascot drawer navigation up to 1024 px, record-detail focus/scroll and a history close action. These supersede the earlier source-preservation statement for those requested UI edits only. Latest UI build and 12 unit tests pass; browser regression is 24 passed / 3 live opt-ins skipped in 13.6 s. No backend changes were needed for this refinement.
