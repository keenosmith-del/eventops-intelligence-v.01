# EventOps Intelligence — React frontend

React/Vite, React Router, native fetch and React Flow. Premium neutral workspace styling with responsive layouts, labeled controls, focus indicators and reduced-motion support. No Axios or browser-side provider keys.

## Setup

```bash
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

Open http://127.0.0.1:5173/ and select **Start**, then **Enter workspace**. Requires the migrated/indexed backend on port 5050. Node 22.12+ or 24 is supported (verified with 24). See the root README for PostgreSQL and FastAPI setup.

| Setting | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | Public backend origin, empty for same-origin local proxy |
| `API_PROXY_TARGET` | Optional Vite server process override; default `http://127.0.0.1:5050`, not embedded as frontend configuration |

Vite development/preview proxy `/api` and `/health`; static `dist` does not include that proxy. Static hosting needs `VITE_API_BASE_URL`, exact backend CORS and SPA rewrites. Do not place Gemini, Mailtrap or PostgreSQL credentials in VITE variables. Rebuild after changing a public API URL.

## Views

- `/`: full-screen editorial introduction with the existing mascot head, staged fades and reduced-motion support.
- `/signin`: translucent **Enter workspace** entry with the existing full-length mascot; creates an anonymous demo session through the unchanged API, not account authentication.
- `/workspace`, `/conversations/:uuid`: Knowledge Assistant with persisted questions/messages, recent history, UUID restore, optional Gemini, distinct evidence/answer presentation and right-side Evidence/Context tabs. Context is the actual query resolution; no general persistent-memory capability is invented.
- `/agents`, `/agents/runs/:uuid`: actual run trigger, configured tool state, persisted node statuses, selectable inputs/outputs/timestamps/errors and verification results. A blueprint without a selected run claims no completion status.
- `/verification`, `/verification/:uuid`: result table, filtering, duplicate/missing/conflict flags, provenance/reference detail and actual CSV export.
- `/history`, `/history/:uuid`: recent persisted executions and restored graph/results.
- `/sources`: indexed file counts, embedding state, content and original source references. Upload is not implemented because there is no ingestion endpoint.

The sidebar collapses into an icon rail with accessible tooltips; its preference persists locally. At mobile/tablet widths up to 1024 px it becomes a mascot-triggered drawer with focus trapping, Escape dismissal and focus restoration. Recent actual chats and New chat appear when the Knowledge Assistant is active. Settings contains the health-check state and closes on outside click or Escape. The sidebar mascot returns to the Knowledge Assistant. Tooltips appear only in the collapsed desktop rail.

Phase 1 refinements use simple left/right arrows, frosted-white hover/focus tooltips and an understated shared workspace footer. The supplied `mascot-thinking.png` appears in the centered assistant and pending follow-ups; its halo/motion follows actual requests and ends on success or failure. Reduced motion disables it. Entry composition is retained, with the explicitly requested shared footer. Graph icons reflect persisted statuses; recorded durations come from timestamps. History shows saved record counts/tool categories, and Sources shows actual types/indexing state. Missing summary values are explicitly not recorded.

Type a first question and press Enter or the integrated arrow: the app creates a real conversation with a deterministic question-derived title, then submits through the existing message API. Shift+Enter inserts a newline. If creation succeeds but message submission fails, the saved conversation and draft remain available for retry without creating another chat. The plus button opens actual indexed sources; uploads remain unavailable. Evidence opens alongside a desktop exchange and through an inspection action on smaller screens. Context displays retained event/query information, never a general memory claim.

The graph pans/zooms and fits its container on resize; every stage also has a keyboard-accessible selection button. Actual inputs/outputs render as readable fields. Tables scroll horizontally on narrow screens; Missing details filters real missing-field discrepancies.

## Execution progress, replay and results

A run starts through the existing POST endpoint and navigates to its returned UUID. Detail polling begins immediately, then repeats every 350 ms while pending/running. Only persisted running stages animate; reduced motion disables animation. Selection follows the active stage, or latest completed stage, until manually overridden. **Follow progress** resumes automatic selection. Source branches show data convergence; the backend reads Calendar, Email and Web sequentially.

Finished runs with recorded timestamps offer **Replay execution**. The recorded clock projects pending/running/final stage states, with pause, speed, timeline seeking and return-to-complete controls. Replay sends no tool calls or new run request. Future outputs remain hidden in stage detail. Saved results remain saved results throughout replay. Historical terminal steps lacking timestamps explicitly say `time not recorded`; replay cannot reconstruct them. CSV export is a separately recorded stage and can extend the timeline after the verification run finishes; repeated exports retain the backend's latest export timestamps.

Results show persisted raw extraction values, normalized values, authoritative reference fields and individual comparison decisions. Older runs without these additive fields explicitly say they were not recorded. **Retrieved (parsed)** counts extraction records, not network responses or every item returned by a remote API. Source contribution in CSV analysis counts each record once per contributing source, so totals can exceed deduplicated records. Missing/conflict counts count affected records, not individual issues. Filters never alter CSV analysis or exported saved records.

Sidebar tooltips use one active state: pointer leave, any click, outside click, navigation, Escape and window blur dismiss them. Keyboard focus can reveal them; ordinary mouse focus does not leave them open.

## API behavior

Conversation requests retain `question` (1–500 chars), `top_k` (1–20), `generate_answer`. The message endpoint returns only the new exchange. Generation statuses are rendered directly: `not_requested`, `generated`, `unavailable`, `insufficient_evidence`. Stored answers use citation pairs in `answer.evidence`, while retrieval messages contain full evidence. After refresh, historical unsuccessful generation status is unknown because the existing backend does not store it; the UI says so explicitly.

Demo tokens are stored only in the current tab's session storage and sent in `X-Demo-Session`. A 401 returns the reviewer to entry. This is session isolation for a synthetic demonstration, not identity authentication. Public `DEMO_MODE=true` filters access by token; local mode can show prior shared synthetic records. Leaving/replacing the session does not restore its old owned records automatically.

Tool connection `configured` is not a successful connection claim. Run step records establish completed/failed/skipped status. Mailtrap is explicitly not connected until configured. A partial run can have useful saved results while a tool is missing; positive fixture data is never substituted into that real run. Export returns a Blob from the actual CSV endpoint and triggers browser download. Verified-only export can be empty.

Reads are aborted on route change. Fetch timeouts are 90 seconds, health 8 seconds and conversation list 15 seconds. Writes are never retried automatically. A timeout can occur after server-side work has started; reopen saved history before retrying. Agent detail polling stops on terminal state or unmount. Same-tab locks prevent duplicate clicks, while backend admission controls cover concurrent runs.

## Tests

```bash
npm run build
npm test
npx playwright install chromium
npm run test:e2e
# Backend must be started with GEMINI_ENABLED=false:
RUN_LIVE_API=true npm run test:e2e
# Existing Google Chrome:
PLAYWRIGHT_CHANNEL=chrome RUN_LIVE_API=true RUN_LIVE_ENTRY=true npm run test:e2e
```

For an isolated preview/backend:

```bash
npm run build
API_PROXY_TARGET=http://127.0.0.1:5052 npm run preview
TEST_BASE_URL=http://127.0.0.1:4173 PLAYWRIGHT_CHANNEL=chrome RUN_LIVE_API=true RUN_LIVE_ENTRY=true npm run test:e2e
```

Workspace redesign verification: build passed, **8 API client tests**, **19 browser tests** including live RAG follow-ups, sidebar history reopening, real reviewer sessions, real Calendar/Web/Mailtrap reads, CSV and execution history. The final focused chat rerun passed **11 tests** after responsive/history refinements. Generated answers and successful answer citations are explicitly fixture-tested; live tests verify Gemini is disabled and report `unavailable`. The real agent run completed all three tool reads; Mailtrap returned zero messages, so live email record processing is still pending a controlled message. Browser CSV exports go to `/tmp`; selected actual screenshots are in `docs/submission/workspace-redesign/`. No live Gemini request is made by these checks. See [visual audit and exact results](../docs/testing/WORKSPACE_REDESIGN.md).

Latest application expansion checkpoint: **22 browser tests passed in 14.0s**, **8 API-client tests passed**, production build passed, backend regression **191 passed / 1 skipped**. New tests cover actual graph-node rendering/clicks and mobile visibility, request-bound mascot success/failure, all rail tooltips, footer landmarks, operational page overflow and actual session exit. See [Phase 1 results and compliance report](../docs/testing/APPLICATION_PHASE1.md). Uploads and workflow expansion remain later phases pending review.

Part 2 production build, **12 unit tests** and **25 Chrome browser tests in 24.2 s** pass with live opt-ins. Latest verification and exact limitations: [Part 2 report](../docs/testing/PART2_EXECUTION.md).

## Structure

- `src/App.jsx`: reviewer entry and shared shell/routes.
- `src/api.js`: native-fetch client, demo header, timeouts and CSV.
- `src/components/KnowledgeAssistant.jsx`: automatic chat creation, composer, evidence/context.
- `src/components/WorkspaceSidebar.jsx`: icon rail/drawer, actual recent chats, settings and session controls.
- `src/components/Exchange.jsx`, `Evidence.jsx`: answers, citations and source panels.
- `src/components/AgentWorkspace.jsx`: run polling, actual graph, node detail, results and exports.
- `src/components/KnowledgeSources.jsx`: live indexed-source view.
- `src/styles.css`, `workspace.css`: existing base styles; `workspace-redesign.css` contains workspace-scoped tokens and refinements, leaving entry pages unchanged.
- `tests/`: API behavior and browser journeys.

## Media and deployment

Actual evidence is in `docs/submission/screenshots/` and `sample-verification.csv`. Recordings directory is prepared but no recording exists. Public URL/recording placeholders remain in the root README. Follow [deployment instructions](../docs/deployment/README.md); hosted integration/cold-start/memory verification and activation of Mailtrap remain owner actions.


## Latest interaction refinements

Every route, including entry pages, uses the same one-line footer: `October 2026 © EventOps Intelligence v.01`, with the workspace metadata typography and no icon. Agent inputs use compact pill surfaces with subtle keyboard focus; Run verification moves slightly upward and darkens on hover. Inspect record scrolls/focuses its evidence section. Close execution returns history to its saved-run list without deleting anything. Empty-chat example questions fill the composer and focus it; submission remains an explicit user action.

Latest UI refinement checks: production build passed, **12 unit tests passed**, **24 browser tests passed in 13.6 s / 3 live opt-ins skipped**. Coverage includes identical footer typography, collapsed-only tooltips, outside-click settings dismissal, phone/tablet mascot navigation, example drafts, thin controls, inspection scrolling/focus and closing history details. Backend code was unchanged in this refinement.
