# Validation evidence — 11 October 2026

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
