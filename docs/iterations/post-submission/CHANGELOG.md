# Changes

## Stage 0 — 11 October 2026

Isolated main in `feature/post-submission-evolution` at the requested next-iteration path. Kept v.01/v.02 intact. Added independent Vite ports/proxy, Playwright ports, Compose project identity, database port and example database name. Fresh ignored credentials, independent dependency installations and database volume. Migrated four schema versions and indexed 19 records/embeddings.

## Stage 1 — interaction polish and connected navigation

- Sidebar UUID search is a controlled, upward floating frosted popover. It reserves no extra layout height, autofocuses its field, supports outside-click/Escape/close dismissal, restores trigger focus on explicit dismissal, and exposes validation accessibly.
- Chat anchors pending follow-ups and completed answers to the user's question. Historical restoration starts at the latest question. Completion focuses the composer without scrolling it into view. An explicit latest-message button appears when the end is below the viewport.
- Composer background uses a masked backdrop blur and translucent gradient. Turn spacing and the end marker allow every answer to scroll clear of it. Motion respects reduced-motion preferences.
- Input/select/textarea focus uses a quiet grey-green one-pixel outline and soft halo. Composer focus is drawn around its rounded surface, retaining a visible accessibility cue.
- Generated answers have a real clipboard copy action with success/failure feedback.
- Knowledge Sources explains reference knowledge versus incoming observations and links to the assistant. Agent links carry event/conversation context in the URL; originating conversations and selected execution IDs remain available across graph/results/history views.
- Deferred initial execution reads avoid duplicate requests from React development trial mounting. No backend graph/timing mutation was introduced.
- Added browser regressions for popover geometry/dismissal, question anchoring, latest navigation, blur/focus, mobile width, context preservation and clipboard operation. Updated opt-in live selectors and assertions to verify saved state remains unchanged after export/history.

Modified implementation files: `compose.yaml`, `.env.example`, frontend Vite/Playwright settings, WorkspaceSidebar, KnowledgeAssistant, Exchange, KnowledgeSources, AgentWorkspace, workspace-redesign.css, workspace/agent browser suites. Documentation resides here. No runtime response fixtures were added; fixtures are confined to automated tests.

## Consolidation — 11 October 2026

The owner corrected the development structure: one evolving application in the original v.01 repository. Both checkouts were clean; no main commits followed the shared ancestor. Fast-forward integration preserved the original Phase 1 commits without cherry-pick duplicates. Restored the original Compose identity, Vite/Playwright ports and example environment; original credentials and volumes remain untouched. Added accurate assessment-demonstrated and pre-iteration tags, updated future instructions and documentation links. No Phase 2 work or remote push occurred. Temporary ignored local settings are preserved outside Git, and the temporary database volume is retained.

Consolidation validation passed: 217 backend / 16 frontend unit / 29 browser regression / 3 live checks and build. Original recording checksums verified. Corrected the live missing-field count assertion for real provider data and saved new evidence in a separate consolidation subfolder.

Verified retirement: `git worktree remove` completed successfully after consolidation commit `250a4a2`. `git worktree list` now contains only the original v.01 checkout. The temporary directory is gone; `feature/post-submission-evolution`, both Phase 1 commits, the ignored settings backup and the stopped temporary database volume are preserved. The unrelated v.02 project was not modified. No remote push or production deployment occurred. The repository is ready for Phase 2, which has not started.


## Phase 1 control styling audit — 11 October 2026

Replaced all seven native dropdowns (agent event, four result filters, chat source count and replay speed) with a shared StyledSelect. Both pill trigger and floating option menu now use rounded corners, cream surfaces, restrained selected-state color and a light shadow. The portal prevents clipping in toolbars/scroll containers; placement flips above when needed and updates before paint after a viewport resize. Keyboard arrows, Home/End, typeahead, Enter/Space, Escape and Tab work; selection still updates real query/run/filter/replay state. No component library added.

Removed the UUID field border and native focus outline; retained a soft grey-green focus halo. Close X buttons have transparent backgrounds and zero border/shadow on hover. The subsequent owner correction removes rotation and all transitions/animations from every close X: hover applies only an immediate 1.08 scale and slight grey-green color shift. Keyboard focus remains visibly light. Audited all form controls, sidebar popovers, chat/context, result filters, agent forms, replay and history surfaces; full-screen backdrop and transparent inner composer text areas retain their intentional geometry.

Saved executions now occupy a bounded scroll region (330 px desktop, 290 px mobile), with two desktop columns, one mobile column, actual count/scroll hint and a selected-run highlight. Every returned run remains accessible by mouse, touch and keyboard. Opening saved runs retains the existing journey query context.

Validation: 16 frontend unit tests, 31 browser regressions (3 opt-in skips), 217 backend tests (1 skip), two actual local entry/RAG checks and build pass. Visual QA of actual local UI is recorded in `evidence/control-audit/`. No production push or Phase 2 feature work.
