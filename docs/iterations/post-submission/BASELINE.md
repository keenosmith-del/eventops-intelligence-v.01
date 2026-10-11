# Submitted baseline

Source commit: `93379eafd445705b0ca678d906031d6f6d0305d5`, clean local main at isolation. origin/main resolves to the same commit. A fresh remote fetch and deployed artifact fingerprint were not performed; this identifies the repository baseline, not an independently confirmed production image.

Architecture: React 19/Vite; FastAPI/Python 3.12; PostgreSQL/pgvector; 384-dimensional FastEmbed retrieval; optional Gemini generation; persisted conversations; LangGraph verification; Calendar/Web read-only HTTP sources and server-configured Mailtrap sandbox; Neon/Render production configuration retained.

Retained assessment capabilities: EVT-101 reference retrieval and POL-003 check-in citation, contextual follow-ups, Ada active-participant positive verification and duplicate provenance merging, inactive/name mismatch flagging, field comparisons, execution history/replay, stored-record CSV export, reviewer session isolation. These scenarios are described in the existing submission evidence. This iteration did not resend Mailtrap messages or invoke a billable model.

Existing tests: Python pytest, Vitest API/execution tests, Playwright introduction/workspace/agent tests; opt-in live external checks. The unchanged backend suite was run against the fresh isolated indexed database: 217 passed, 1 skipped. Initial execution before starting Docker had database connection failures; after migration and indexing the full suite passed.

Known limitations: fixed seeded knowledge; no session uploads; background tasks are not durable workers; no general adaptive extraction; public holiday providers are unrelated to EVT-101; generation is optional and disabled locally; Mailtrap credentials absent in this new environment; no live-generated Gemini answer verified in this iteration.
