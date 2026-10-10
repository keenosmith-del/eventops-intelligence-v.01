# Application expansion — Phase 1 review

10 October 2026. This increment completes the shared workspace and remaining-page visual refinement. Work stops here for user review, as requested. It does not claim completion of the later upload, verification-intelligence or n8n phases.

## Delivered and preserved

- Shared workspace footer uses the exact two requested lines, with the Lucide Brain icon. It sits in document flow beneath content; it never overlays the composer, graph or tables.
- Sidebar uses ArrowLeft/ArrowRight, keeps `/mascot-head.png`, and has frosted white hover/focus tooltips for every collapsed navigation item, New chat, expansion, Settings and Leave session. Mobile tooltips remain inside the drawer. Leaving clears the current tab's reviewer credential and returns to sign-in.
- Centered assistant uses the supplied `/mascot-thinking.png`. Pending requests apply a soft halo and restrained head motion; follow-ups show a small pending mascot. Status is “Reviewing sources”, with an answer-request qualifier when selected. The existing blocking API exposes no separate generation phase, so the UI does not invent one. Success and failure both end the thinking state. Reduced motion disables all mascot/halo motion.
- Agent stages use subtle icons for persisted pending/running/completed/failed/skipped states. Inputs, outputs, provenance and errors remain inspectable; duration is derived only from recorded start/finish timestamps. Memoized graph nodes/edges avoid unnecessary layout resets. Browser checks now inspect and click actual React Flow nodes, including mobile visibility, rather than relying solely on stage buttons.
- Results retain actual persisted counts, missing-field filtering, evidence/reference detail and both real CSV actions. Absent summary values say “Not recorded”; empty filtered results have an explicit message.
- History has clearer spacing and recorded result counts/tool categories. Attempted tools are labeled as tools, not as evidence of records from an empty inbox. Loading and connection failure are distinct from an empty history.
- Source rows show actual filename/type, record types, record and embedding counts, indexing state and original provenance. No last-index timestamp is invented; the current API does not expose one. Uploads remain explicitly unavailable until their separate implementation phase.

The approved introduction component and stylesheet are byte-for-byte unchanged from the start of this increment; their existing footer is preserved. The new Brain footer is confined to application workspace routes. No backend, API client, data model, provider, dependency, reference data or security setting changed in this increment. Earlier uncommitted work was retained. No commit or push was made.

## Exact final checks

| Check | Result |
| --- | --- |
| `npm run build` | Passed: 2,104 modules; JS 492.93 kB / 158.41 kB gzip; CSS 60.70 kB / 12.27 kB gzip |
| `npm test` | 8 passed |
| Chrome browser suite, both live flags enabled | **22 passed in 14.0s**, no skips |
| `GEMINI_ENABLED=false .venv/bin/python -m pytest -q --tb=no` | **191 passed, 1 skipped in 1.70s**; controlled Mailtrap test is opt-in |
| `git diff --check` | Passed |
| Approved entry pages | Unchanged file hashes; desktop/mobile browser regression passed |

Browser command, from `frontend/`, against the existing Gemini-disabled local backend on 5052 through preview on 4173:

```bash
TEST_BASE_URL=http://127.0.0.1:4173 PLAYWRIGHT_CHANNEL=chrome RUN_LIVE_API=true RUN_LIVE_ENTRY=true npm run test:e2e
```

Live conversation: `2b66a2d7-da74-4f78-aa3a-5bacc6850e67`. Original EVT-101 venue question and check-in follow-up persisted as four messages, with inherited event context and `POL-003` provenance preserved through reload/sidebar/UUID restore. Requested generation returned `unavailable`; zero generated answers were saved. No Gemini provider request occurred.

Live execution: `84d16ce9-7bdf-49c2-a324-3c980a89ad46`. Calendar, Web and Mailtrap HTTPS reads completed. Mailtrap reported zero messages and zero bytes, which is an empty read, not successful email extraction. Persisted results contained 16 review-required holiday observations, zero verified records and 11 duplicates merged. CSV download, restored graph and history passed. Real holiday sources were not treated as fictional EVT registrations.

Actual screenshots were inspected after capture: [Phase 1 graph desktop](../submission/workspace-redesign/phase1-graph-desktop.png), [graph mobile](../submission/workspace-redesign/phase1-graph-mobile.png), [agent desktop](../submission/workspace-redesign/phase1-agent-desktop.png), [agent mobile](../submission/workspace-redesign/phase1-agent-mobile.png), [results](../submission/workspace-redesign/phase1-results-desktop.png), [sources](../submission/workspace-redesign/phase1-sources-desktop.png), [history desktop](../submission/workspace-redesign/phase1-history-desktop.png), [history mobile](../submission/workspace-redesign/phase1-history-mobile.png). Pending-state checks use explicitly gated test API responses; these are not live generation evidence. Earlier screenshots in that directory remain historical snapshots.

Additional actual reviewer-session captures: [welcome desktop](../submission/workspace-redesign/phase1-welcome-desktop.png), [welcome mobile](../submission/workspace-redesign/phase1-welcome-mobile.png), [frosted tooltip](../submission/workspace-redesign/phase1-frosted-tooltip.png). These required no conversation submission or external tool execution.

## Assessment compliance at this checkpoint

“Externally verified” below means actual external provider HTTPS reads executed locally, not hosted deployment or independent assessment approval. No application feature is claimed as Deployed.

| Requirement | Status | Evidence / remaining limit |
| --- | --- | --- |
| Part 1: three structured sources, real embeddings, semantic retrieval | Implemented; Locally verified | Original 19 PostgreSQL/pgvector records preserved; live source view and RAG journey |
| Query transformation and contextual follow-ups | Implemented; Locally verified | Supported event-context inheritance, original question and inspectable resolution; broader follow-up expansion remains a later phase |
| Grounded generation and source citations | Implemented; Locally verified | All four generation states/citations fixture-tested; live regression uses Gemini disabled and verifies `unavailable`. Prior generation evidence is documented separately |
| Persistent conversation history | Implemented; Locally verified | Real reload, sidebar reopen and UUID restore |
| Unified frontend and operational resilience | Implemented; Locally verified | Build, 22 browser checks, responsive views, request errors, keyboard/focus, reduced motion and session exit |
| Part 2: Calendar / Email / Web reads | Implemented; Externally verified | Real HTTPS reads; Calendar/Web records processed; Mailtrap inbox empty |
| Email body extraction through real Mailtrap | Still blocked | Owner must insert controlled email; bounded opt-in test and instructions already prepared |
| LangGraph extraction, cleansing, deduplication and reference verification | Implemented; Locally verified | Existing bounded deterministic pipeline, stored node decisions/results; synthetic positive/discrepancy tests remain distinct from live holidays |
| Execution graph, results, history and CSV | Implemented; Locally verified | Actual node visibility/clicks, saved data and export; expanded analysis filters/raw-reference comparison are reserved for later phases |
| Session isolation, bounded providers, restricted CORS and secrets | Implemented; Locally verified | Existing backend controls and regression tests retained; credentials remain server-side |
| Session-scoped CSV/JSON uploads and new-source retrieval | Still blocked | Not implemented in this phase; next incremental work after review; authoritative references must remain separate |
| Generalization to unseen inputs / optional structured model extraction | Still blocked | Existing narrow deterministic formats remain; expanded unseen scenarios await their implementation phase |
| Real n8n automation and idempotent service integration | Still blocked | `automations/` contains only an empty README, no importable workflow; implementation/configuration reserved for later phase |
| Public application and recording | Still blocked | Deployment and recording absent; existing setup blueprint and placeholders retained |

Next increment after review: genuine bounded, session-scoped CSV/JSON ingestion, persistent embeddings/provenance, safe deletion and retrieval/citation tests using an unfamiliar document. Then unseen-input verification, followed by protected and idempotent n8n integration. No later-phase endpoint or simulated success was added here.
