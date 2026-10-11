# EventOps Intelligence — Complete Application Walkthrough

**Recording:** [eventops-complete-walkthrough.mp4](../recordings/eventops-complete-walkthrough.mp4)  
**Duration:** 3 minutes 36.23 seconds  
**Application:** [EventOps Intelligence](https://eventops-intelligence.onrender.com)  
**Capture:** 11 October 2026 · production release `7cc6568`  
**Format:** Silent H.264 MP4 · 1920 × 1080 · 30 fps

## Non-technical explanation

This recording follows the complete reviewer journey: entering the application, finding an event rule, checking incoming registration information, examining the evidence behind decisions, downloading results and returning to a saved execution.

The reviewer begins on the landing page, selects **Start** and enters the workspace without creating an account. The sidebar makes the main areas available: Knowledge Assistant, Agent Workspace, Verification Results, Execution History and Knowledge Sources.

In the Knowledge Assistant, the reviewer asks, **“What time does check-in close for EVT-101?”** The application retrieves policy **POL-003**, which states that check-in closes at **08:45 South Africa Standard Time**. Opening the policy reveals its wording and source location, allowing the reviewer to check the deadline directly. The screen labels this interaction as **evidence only**: the application is displaying supporting information rather than a newly written Gemini answer.

The follow-up, **“What time does its check-in close?”**, demonstrates that the assistant can carry the event reference into the next question. The context panel identifies EVT-101 as the inherited event. The reviewer then opens a new chat and returns to the saved conversation through the sidebar history, demonstrating that the earlier questions and evidence remain available.

The reviewer next selects EVT-101 in the Agent Workspace and starts a bounded verification run. The workflow shows genuine progress as the application reads Calendar, Email and Web sources. The Email integration reads three existing synthetic assessment messages from Mailtrap; it sends no new messages.

The completed results distinguish confirmed registrations from information requiring review. **Ada Mensah** is verified against the reference records. Her positive registration and duplicate message are combined into one result, with both pieces of evidence retained. **Lindi Mokoena-Test** is flagged because the reference participant is inactive and the submitted name differs from the reference name. External calendar and web observations are separately flagged because they lack an event identifier needed to establish an EVT-101 match.

Finally, the reviewer downloads all results and the verified-only results, then restores the same completed execution from history. The overall demonstration shows how an event operator can move from a question to a traceable decision and retain the information needed to explain that decision later.

## Technical explanation

### Retrieval and conversation persistence

The footage visibly demonstrates natural-language questioning, event-aware evidence retrieval, source provenance, deterministic follow-up context and restoration of a saved conversation. POL-003 exposes the source reference `data/structured/policies.csv#policy_id=POL-003` and the document `policies.csv`.

The supporting implementation uses the conversation API, rule-based query interpretation, local query embeddings and PostgreSQL/pgvector retrieval. Follow-up resolution uses stored conversation messages to associate “its” with an unambiguous event. The original user question is retained, while the enriched retrieval query and inherited event are recorded separately. These implementation details explain the observed behavior; the recording itself does not expose database administration or vector calculations.

New requests use `generate_answer=false`. Consequently, this recording demonstrates the retrieval and evidence-tracing components of the RAG workflow, not a new generated-answer evaluation.

### Orchestration and verification

The demonstrated run is `e5f325b2-03e3-4da5-8636-cdc894d0ed2b`, with execution mode `real_https_read_only`, reference event EVT-101 and a limit of 20 records per source. Mailtrap independently caps reads at three messages.

LangGraph executes the following processing sequence:

**Trigger → Calendar → Email → Web → Extraction → Normalization → Deduplication → Verification → Discrepancy handling → Persistence.**

The source reads execute sequentially, although the graph visually groups their contributions. The workflow is deterministic and bounded; it does not use an LLM to choose tools or conduct an open-ended reasoning loop. The application records stage states, timestamps, inputs and outputs in PostgreSQL, which the frontend retrieves to display execution progress and saved history.

| Saved outcome | Result |
| --- | --- |
| Calendar, Email and Web tools | All completed |
| Mailtrap assessment messages read | 3 |
| Claims extracted and normalized | 30 |
| Records after duplicate merging | 18 |
| Duplicates merged overall | 12 |
| Verified records | 1 — Ada |
| Flagged records | 17 — Lindi plus 16 external observations |

Verification compares normalized claims with indexed event and participant references. Ada has no recorded discrepancy and retains two observed email records with a duplicate count of one. Lindi carries the issue codes `inactive_participant` and `name_mismatch`. The system does not fill missing event IDs with the selected run target merely to create a match.

### Exports, history and interpretation limits

The actual [full CSV](../exports/eventops-full.csv) contains 18 data rows, and the [verified-only CSV](../exports/eventops-verified.csv) contains Ada's single verified row. Restoring execution history retrieves the existing run and its persistence details; it does not start another tool execution.

The graph's CSV node remains **pending** after the downloads. Exports are separate API operations and do not mutate the recorded processing timeline. Both downloads succeeded, but no operating-system save dialog appears in the browser recording.

“Completed” describes the workflow outcome, not universal acceptance of its input records. “Verified” describes a match against this assessment's authoritative references, not proof of real-world identity or attendance. The footage uses synthetic registration records and demonstrates one bounded execution, rather than load testing or production-scale reliability.

## Supporting evidence

- [Landing](../screenshots/landing.png), [Knowledge Assistant](../screenshots/knowledge-assistant.png) and [completed workflow](../screenshots/agent-workflow.png).
- [Verification results](../screenshots/verification-results.png), [Ada's decision](../screenshots/ada-verified.png), [duplicate evidence](../screenshots/duplicate-evidence.png) and [Lindi's conflict](../screenshots/lindi-conflict.png).
- [Restored execution history](../screenshots/execution-history.png) and [recording metadata and checksums](../recordings/manifest.json).
