# Workspace visual audit — 2026-10-10

The approved landing and sign-in components, their CSS, routes and reviewer session API were preserved. No backend file, API contract, provider adapter or dependency changed during this workspace pass. No commit or push was made.

## Delivered behavior

- Workspace shell: mascot wordmark, five Lucide navigation items, soft active states, minimal page-context header. Removed numbered navigation, slogans, uppercase styling, decorative status dots and permanent connection refresh.
- Sidebar: persisted desktop collapse preference, recognizable avatar/icon rail and hover/focus tooltips. Actual recent chats appear beneath navigation. New chat starts an empty composer. UUID restore remains in a compact disclosure; Settings contains health status/version and session exit. Mobile drawer traps focus, closes with Escape and restores opener focus.
- Knowledge Assistant: mascot, exact conversational heading/description and integrated multiline composer. Enter submits, Shift+Enter adds a newline; same-tab lock and disabled state prevent duplicate submissions. First question creates a scoped real chat with a deterministic title (maximum 120 characters) and calls the existing message API. No title field or title-generation provider request. A failed first message retains its created chat/draft for retry.
- Evidence/context: no empty side panel. Desktop exchanges open actual record evidence; narrow screens offer inspection on demand. Record IDs, source documents/references, excerpts and actual retrieval scores remain visible. Context reports the real retained event/query decision. Generated answers/citations, unavailable/insufficient evidence and historical uncertainty remain distinct. No internal query-plan JSON is shown.
- Sources menu: actual indexed documents from the existing source API. No upload endpoint exists; uploads are explicitly unavailable. Links open the source records/provenance.
- Other views: direct operational headings, rounded graph stages with actual statuses, unnumbered stages, readable execution input/output fields, restrained result summaries/tables, missing-field filtering, real CSV exports, clean saved execution lists and source rows. No simulated success or placeholder history.
- Styling: all new tokens/selectors are scoped to `.app-shell` in `workspace-redesign.css`. Approved introduction styles remain independent. Mascot float is four pixels over seven seconds; reduced motion disables it.

## Exact validation

- Frontend API/client tests: **8 passed**.
- Production build: **passed**, 2,104 modules, final JS 490.10 KB / 157.64 KB gzip; CSS 58.64 KB / 11.84 KB gzip.
- Expanded Chrome browser suite against local public-mode backend: **19 passed in 11.6s**, no skips, with `RUN_LIVE_API=true` and `RUN_LIVE_ENTRY=true`.
- Final chat-only rerun after responsive/history corrections: **11 passed in 5.1s**, including real API follow-ups/history. Other operational views were unchanged by those corrections.
- Backend regression suite (unchanged code): **191 passed, 1 skipped in 1.48s**. The opt-in controlled Mailtrap message test remains skipped in the regular suite.
- `git diff --check`: passed.

Browser coverage includes reviewer entry, desktop/mobile entry navigation, empty chat, four explicit generation-state fixtures, source/citation inspection, first-message creation failure/retry without duplicate chats, Enter/Shift+Enter, indexed source menu, persisted collapse preference, accessible rail tooltip, mobile drawer/Escape focus return, request validation, real conversation persistence/context/history, real agent execution/export/history, and source counts/details.

### Live evidence

Latest live chat verification: `32d869ee-a07f-4a59-b4f5-55984ea28ef7`. First question “Where is EVT-101 being held?” became its title. Follow-up “What time does its check-in close?” retained EVT-101 context and original wording, with `POL-003` and `data/structured/policies.csv#policy_id=POL-003`. Four persisted messages and zero generated answers; generation was explicitly disabled and returned `unavailable`. Database reload, actual sidebar selection and UUID restore passed.

Latest live agent verification: `0c74e77c-51e0-4ef0-8f53-60e44cd105c2`. Calendar/Web/Mailtrap reads completed, followed by actual graph persistence, CSV export and execution-history reopening. Real public holiday observations yielded **16 flagged records**, **0 verified**, **11 duplicates merged**. Mailtrap was connected but empty; a completed empty read is not email record-processing evidence. The controlled email insertion/test remains separately documented in [MAILTRAP_INTEGRATION.md](MAILTRAP_INTEGRATION.md).

No live Gemini provider call was made. Successful generated answers/citations remain fixture coverage rather than a new live generation claim. Public demo tokens scope these retained test records; another reviewer session cannot open them by UUID.

## Visual review

Actual final screenshots, captured through real local API sessions: [workspace-redesign artifacts](../submission/workspace-redesign/). Includes desktop/mobile empty chat, populated conversation/history, desktop icon rail, mobile drawer, loaded indexed sources, empty verification results and actual execution history/results. No synthetic screenshot data was substituted.

Existing limitations remain: document uploads are unavailable; Mailtrap has no message to process yet; the agent is deterministic LangGraph orchestration; public deployment and recording are outside this visual pass. There are no new implementation blockers.

## Files changed in this pass

`frontend/src/App.jsx`, `components/KnowledgeAssistant.jsx`, `WorkspaceSidebar.jsx` (new), `Exchange.jsx`, `Evidence.jsx`, `AgentWorkspace.jsx`, `KnowledgeSources.jsx`, `workspace-redesign.css` (new), `workspace-errors.js` (new); browser tests updated for intended controls/labels and expanded chat coverage; frontend/root README and this audit; actual screenshot artifacts. Earlier uncommitted introduction/dependency changes remain intact and were not redone.
