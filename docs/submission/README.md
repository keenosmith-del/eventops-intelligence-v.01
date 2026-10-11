# EventOps Intelligence — final assessment evidence

[Live application](https://eventops-intelligence.onrender.com) · production release `7cc6568` · captured 11 October 2026 (South Africa Standard Time).

## Silent recordings

All three recordings show the actual deployed application in a clean Chromium reviewer context at **1920 × 1080, 30 fps, H.264 MP4**. They are ready for captions or narration; no audio, overlays, synthetic UI, mocked responses or artificial progress were added.

| Recording | Duration | Size | Contents |
| --- | --- | --- | --- |
| [Complete walkthrough](recordings/eventops-complete-walkthrough.mp4) | 3:36.23 | 3.99 MB | Landing, Start, reviewer entry, primary navigation, retrieval and conversation history, real execution, evidence, CSV downloads and restored execution history. |
| [Part 1 — RAG](recordings/eventops-rag-demonstration.mp4) | 1:10.50 | 0.92 MB | Natural-language question, POL-003 and 08:45 SAST deadline, source reference, contextual follow-up, inherited EVT-101 context, new chat and history restoration. |
| [Part 2 — agent verification](recordings/eventops-agent-verification.mp4) | 1:58.27 | 2.61 MB | Bounded real execution, live progress, Calendar/Email/Web outcomes, participant checks, duplicate evidence, conflict detection, flagged observations, exports and saved history. |

The focused recordings are excerpts from the complete capture. Generation remained unchecked: new responses are explicitly **evidence only**, not newly generated Gemini answers. No billable generation request was made.

## Recording write-ups

Each Markdown file combines a non-technical explanation with a technical account of the demonstrated behavior, outcomes and evidence limits.

- [Complete application walkthrough](writeups/eventops-complete-walkthrough.md)
- [Part 1 — RAG demonstration](writeups/eventops-rag-demonstration.md)
- [Part 2 — agentic verification](writeups/eventops-agent-verification.md)

## Production execution demonstrated

Execution `e5f325b2-03e3-4da5-8636-cdc894d0ed2b` used EVT-101 with a bound of 20 records per source and execution mode `real_https_read_only`. The actual LangGraph workflow completed all 10 processing stages. Calendar, Email and Web reads completed; Mailtrap read its three existing synthetic assessment messages without sending email.

- 30 claims extracted and normalized; 18 records saved; 12 duplicates merged overall.
- Ada Mensah verified; one duplicate merged, retaining both positive and duplicate email evidence.
- Lindi Mokoena-Test flagged for `inactive_participant` and `name_mismatch`.
- 16 external Calendar/Web observations remained flagged for missing event IDs; they were not presented as verified EVT-101 registrations.
- [Full CSV](exports/eventops-full.csv): 18 records. [Verified-only CSV](exports/eventops-verified.csv): one record, Ada.
- History restored the same completed run, recorded timestamps, workflow stages and PostgreSQL persistence outcome.

Both exports were downloaded through the application's real buttons and checked. The graph's CSV node remains labelled **pending** after downloads; the deployed UI describes downloads as outside the processing timeline. This visual state is preserved, not changed to imply completion. Browser-managed downloads do not display an operating-system save dialog in the footage; the downloaded files are included above. All requested application interactions were captured.

Two bounded production runs were needed in total: an initial capture stopped at an incorrect automation filter selector, and the replacement used a new isolated reviewer context. Only the replacement run appears in the delivered videos and final screenshots. Earlier failed takes and raw browser video remain outside this submission directory.

## Selected production screenshots

All selected screenshots are actual 1920 × 1080 production browser captures from the final reviewer journey.

| Screenshot | Working state |
| --- | --- |
| [Landing](screenshots/landing.png) | Deployed landing page and Start action. |
| [Knowledge Assistant](screenshots/knowledge-assistant.png) | POL-003 expanded with 08:45 deadline, source and evidence-only status. |
| [Agent workflow](screenshots/agent-workflow.png) | Real completed workflow and all three source outcomes. |
| [Verification results](screenshots/verification-results.png) | Saved counts, discrepancy analysis and flagged external observations. |
| [Execution history](screenshots/execution-history.png) | Same completed run restored with workflow stages and persistence details. |
| [Ada verified](screenshots/ada-verified.png) | Verified decision, duplicate count and both raw email records. |
| [Retained duplicate evidence](screenshots/duplicate-evidence.png) | Passed reference checks and both observed assessment messages. |
| [Lindi conflict](screenshots/lindi-conflict.png) | Inactive participant/name mismatch and field-level decisions. |

Existing screenshots elsewhere in this folder are historical artifacts; the selections above identify this submission's final production evidence.

## Validation and repository suitability

Videos were inspected using timeline contact sheets and full-resolution key frames; every MP4 passed full FFmpeg decoding, with H.264, 1080p, 30 fps and no audio confirmed. Screenshots and CSV row counts were inspected. [Manifest](recordings/manifest.json) records exact byte sizes, durations, checksums and the production run identity.

Each MP4 is under 5 MB and suitable for ordinary GitHub storage without Git LFS. No external hosting is needed. No files were committed or pushed. Application code, production settings, the Executive Technical Brief and the Local Reviewer Runbook were not modified by this task.
