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
