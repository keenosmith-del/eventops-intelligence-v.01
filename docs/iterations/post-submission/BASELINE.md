# Submitted baseline

Pre-iteration repository commit: `93379eafd445705b0ca678d906031d6f6d0305d5`, annotated tag `pre-iteration-v0.1`. This clean main snapshot contains the final submission documentation and three walkthrough recordings.

The submission README and recording manifest identify `7cc65680950fba53caf302c8fe3a8eadb21b0225` as the demonstrated assessment release; annotated tag `assessment-demonstrated-v0.1` preserves that revision. The acceptance README also names its underlying implementation commit `428bd35`. No delivery timestamp or exact submitted archive revision is independently established, so neither tag is misleadingly named assessment-submission. A fresh production fingerprint was not performed.

Architecture: React 19/Vite; FastAPI/Python 3.12; PostgreSQL/pgvector; 384-dimensional FastEmbed retrieval; optional Gemini generation; persisted conversations; LangGraph verification; Calendar/Web read-only HTTP sources and server-configured Mailtrap sandbox; Neon/Render production configuration retained.

Retained assessment capabilities: EVT-101 reference retrieval and POL-003 check-in citation, contextual follow-ups, Ada active-participant positive verification and duplicate provenance merging, inactive/name mismatch flagging, field comparisons, execution history/replay, stored-record CSV export, reviewer session isolation. These scenarios are described in the existing submission evidence. This iteration did not resend Mailtrap messages or invoke a billable model.

Existing tests: Python pytest, Vitest API/execution tests, Playwright introduction/workspace/agent tests; opt-in live external checks. The unchanged backend suite was run against the fresh isolated indexed database: 217 passed, 1 skipped. Initial execution before starting Docker had database connection failures; after migration and indexing the full suite passed.

Known limitations: fixed seeded knowledge; no session uploads; background tasks are not durable workers; no general adaptive extraction; public holiday providers are unrelated to EVT-101; generation is optional and disabled locally; Mailtrap credentials absent in this new environment; no live-generated Gemini answer verified in this iteration.
