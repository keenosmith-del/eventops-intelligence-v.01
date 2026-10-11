# Validation evidence — 11 October 2026

Close X correction: `PLAYWRIGHT_CHANNEL=chrome npm run test:e2e -- --grep 'saved chat search floats'` passed (1 test). With reduced motion disabled, the browser confirms an immediate scale-only transform, zero transition duration, no animation, subtle color shift and no hover border/background. The shared rule covers both UUID search and the evidence-panel X. No backend or database changes were required for this correction.

## Historical Phase 1 checks in the temporary environment

The following evidence describes the initial Phase 1 setup. Its temporary ports/database are historical; current development uses original v.01 settings documented below.

All database-backed checks target only `127.0.0.1:55433`, database `eventops_next`. Gemini is disabled and no email sending occurred. Production was not accessed or modified.

| Check | Command / context | Result |
| --- | --- | --- |
| Isolated DB | `docker compose up -d --wait` | Healthy; dedicated project/network/volume |
| Migration | In backend: `.venv/bin/python -m app.core.migrate` | Four migrations applied to fresh DB |
| Indexing | In backend: `.venv/bin/python -m app.rag.indexing` | 19 records, 19 embeddings, zero pending |
| Backend regressions | In backend: `GEMINI_ENABLED=false .venv/bin/python -m pytest -q --tb=no` | 217 passed, 1 skipped in 7.26s, using independently installed locked dependencies |
| Frontend unit | In frontend: `npm test` | 16 passed |
| Build | In frontend: `npm run build` | Passed; existing >500 kB bundle warning remains |
| Browser regressions | In frontend: `PLAYWRIGHT_CHANNEL=chrome npm run test:e2e` | 29 passed, 3 opt-in live tests skipped |
| Live knowledge/agent | In frontend: `RUN_LIVE_API=true PLAYWRIGHT_CHANNEL=chrome npm run test:e2e -- --grep 'live Journey B\|real API:'` | 2 passed in 5.3s |
| Whitespace / baseline preservation | `git diff --check`; v.01 `git status --short` | Clean |

The system Chrome channel was used because bundled Playwright Chromium was absent. Browser fixture tests remain explicitly fixture-based: generation success/error states, layout geometry, copy, scroll and navigation. They do not establish external provider success or live model generation.

The live knowledge check created conversation `2d6db3ef-6bb9-472f-b4c9-3a71f705ae4b`, persisted four messages, retrieved EVT-101 and contextual POL-003 evidence, restored original question wording/citations, exercised UUID lookup, and confirmed unchanged messages after refresh. Generation status was `unavailable`, as expected with Gemini disabled; zero generated answers.

The live agent check created run `6331164e-d1dc-411a-b60f-d0d9047b0303`, performed actual Calendar/Web reads, recorded Mailtrap as unavailable/skipped without credentials, inspected field-level/raw evidence, verified CSV downloads against API exports, revisited results/history, and confirmed identical saved steps/results after export and refresh. Screenshots are in [evidence](evidence/). The live source observations remain public-holiday data; this is not the planned coherent EVT-101 synthetic scenario.

The independent local DB contains test/live-run data only. Backend assessment tests cover positive/duplicate/inactive/conflicting inputs using their explicit test adapters. No new real Mailtrap message or paid Gemini outcome is claimed.

Initial setup surfaced a stopped Docker daemon, missing bundled browser executable, duplicate development reads, ambiguous repeated-title live selectors and an outdated export-stage expectation. Each was resolved before final checks. A test invocation from the repository root failed imports; the documented/backend-directory invocation passes.


## Consolidation validation in original v.01

Current checkout: `/Users/keenosmith/Programming/Projects/inference-group/eventops-intelligence-v.01`, branch `main`. Original local database port 55432, original credentials and existing `eventops-intelligence-v01_postgres_data` volume. Production URLs/configuration were not used for database validation.

- `docker compose up -d --wait`: original container healthy, existing volume reused.
- Backend migration runner: no new migrations required. Indexing: 19 records, 19 embeddings, zero changed records and zero pending embeddings.
- In backend, `GEMINI_ENABLED=false .venv/bin/python -m pytest -q --tb=no`: **217 passed, 1 skipped in 2.14s**.
- In frontend, `npm test`: **16 passed**. `npm run build`: **passed**, existing bundle size warning retained.
- `PLAYWRIGHT_CHANNEL=chrome npm run test:e2e`: **29 passed, 3 opt-in skips in 21.2s**. Covers UUID popover, chat scrolling/blur/clearance, latest and clipboard actions, preserved context/navigation and refresh.
- `RUN_LIVE_API=true RUN_LIVE_ENTRY=true PLAYWRIGHT_CHANNEL=chrome npm run test:e2e -- --grep 'live Journey B|real API:|real reviewer API'`: **3 passed in 11.2s**, actual frontend at 5173 communicating with original local backend at 5050.
- Live agent run: `a75a9d88-08c2-43dc-8637-55af7a722959`; tool reads, field comparison, CSV/API consistency, history restoration and unchanged saved stages/results verified.
- Live knowledge conversation: `dc150b8c-4888-4d45-b404-0e002e0f1236`; four persistent messages, POL-003 contextual citation, UUID/history/refresh verification. Generation unavailable as expected with Gemini disabled; no paid model call or email sending.
- Three submission recording SHA-256 values match the original manifest. `docs/submission/`, backend and Render configuration match the pre-iteration baseline. Phase 1 frontend source matches `5719f7a` exactly.
- Both worktrees were clean before integration; main had no commits after their shared ancestor. Fast-forward retained `52b9def` and `5719f7a`; no cherry-pick duplicates or history rewrites.
- Corrected live CSV assertion to count records with actual missing-field issues, rather than assuming every real provider observation is incomplete. Consolidation screenshots are saved under `evidence/consolidation/`, preserving earlier evidence.

Sandbox-only attempts to bind/connect localhost were denied; rerunning with approved local network access completed the checks above. No application defect was inferred from those sandbox failures.

Temporary `.env` is preserved in ignored `storage/retired-environments/phase1.env` (mode 0600); original `.env` was not overwritten. Dependency installations, caches and transient test outputs are reproducible ignored artifacts, not untransferred source work. The temporary database volume remains intact. Phase 2 has not begun.

Verified retirement: `git worktree remove` completed successfully after consolidation commit `250a4a2`. `git worktree list` now contains only the original v.01 checkout. The temporary directory is gone; `feature/post-submission-evolution`, both Phase 1 commits, the ignored settings backup and the stopped temporary database volume are preserved. The unrelated v.02 project was not modified. No remote push or production deployment occurred. The repository is ready for Phase 2, which has not started.


## Phase 1 styling audit verification

- `npm test`: 16 passed; `npm run build`: passed (existing bundle warning retained).
- `PLAYWRIGHT_CHANNEL=chrome npm run test:e2e`: 31 passed, 3 opt-in skips in 23.3s. New checks cover rounded option menus, keyboard selection and submitted event configuration, real filter changes, popup bounds at 390px, bounded lists with 20 records, and opening older records on desktop/mobile. UUID regression checks border/focus/close hover styling.
- `GEMINI_ENABLED=false .venv/bin/python -m pytest -q --tb=no`: 217 passed, 1 skipped in 2.32s.
- `RUN_LIVE_API=true RUN_LIVE_ENTRY=true PLAYWRIGHT_CHANNEL=chrome npm run test:e2e -- --grep 'real API:|real reviewer API'`: 2 passed in 2.6s against original local backend. Conversation `b27828d3-dfbc-4527-a7c1-fb5fa6ba439e` retained four messages and contextual citations; generation unavailable as expected with Gemini disabled.
- Actual local preview screenshots visually inspected: `evidence/control-audit/desktop-picker.png`, `desktop-saved-executions.png`, `mobile-saved-executions.png`, `uuid-search.png`. Browser-only regression fixtures remain confined to tests.

The resize regression initially exposed stale popup coordinates; moving placement to a layout effect removed the first-frame stale geometry, and targeted/full regressions then passed. Original backend, deployment configuration and database credentials are unchanged.
