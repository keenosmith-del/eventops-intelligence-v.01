# EventOps Intelligence — Part 2: Agentic Verification

**Recording:** [eventops-agent-verification.mp4](../recordings/eventops-agent-verification.mp4)  
**Duration:** 1 minute 58.27 seconds  
**Application:** [EventOps Intelligence](https://eventops-intelligence.onrender.com)  
**Capture:** 11 October 2026 · production release `7cc6568`  
**Format:** Silent H.264 MP4 · 1920 × 1080 · 30 fps

## Non-technical explanation

This recording shows the application reading information from connected sources, checking registration claims against event and participant reference records, and preserving the reasons behind its decisions.

The reviewer selects **EVT-101** and starts a verification run with a limit of **20 records per source**. The workflow displays actual progress as Calendar, Email and Web reads execute. All three integrations finish successfully. The Email tool reads three existing synthetic assessment messages from the Mailtrap testing sandbox; no new email is sent.

The resulting decisions illustrate three different situations:

1. **A supported registration:** Ada Mensah is marked verified because the relevant event and participant checks pass.
2. **A duplicate submission:** Ada's positive message and duplicate message become one result. Both original pieces of evidence remain available, so merging does not erase the explanation of where the registration information came from.
3. **A conflicting registration:** Lindi Mokoena-Test requires review because the reference participant is inactive and the submitted name differs from the reference name. The detail view shows these issues and the underlying field comparisons.

The Calendar and Web sources also contribute external observations. They are displayed separately as records requiring review because they lack the event identifiers needed to establish a valid event match. Reading a source successfully does not automatically make everything in it a verified registration.

The reviewer downloads two CSV files: all saved results and only the verified result. The full file contains 18 records; the verified-only file contains Ada's single record. The recording ends by opening Execution History and restoring the same completed run, including its workflow stages and saved-result information.

The practical value is an explainable review process: confirmed records can be separated from discrepancies, duplicates can be consolidated without losing evidence, and the completed work can be revisited and exported.

## Technical explanation

### Execution identity and real integrations

The footage demonstrates execution `e5f325b2-03e3-4da5-8636-cdc894d0ed2b`, with reference event EVT-101 and mode `real_https_read_only`. The run reads configured external sources rather than mocked responses or fixture fallback.

| Integration | Actual source behavior | Observed outcome |
| --- | --- | --- |
| Calendar | Reads and parses a remote public iCalendar feed | Completed; 14 parsed claims |
| Email | Reads the Mailtrap sandbox message list and plain-text bodies | Completed; 3 existing assessment messages read |
| Web | Reads configured HTTPS reference data | Completed; 13 parsed claims |

The three email messages represent positive, duplicate and inactive/conflicting registration cases. Their contents are synthetic assessment inputs obtained through the real Mailtrap integration. Real provider access and synthetic business records are therefore both accurate descriptions of the demonstration.

### LangGraph orchestration and recorded state

The supporting implementation builds a LangGraph `StateGraph` with the sequence:

**Trigger → Calendar → Email → Web → Extraction → Normalization → Deduplication → Verification → Discrepancy handling → Persistence.**

Tool reads execute sequentially, even though the visual graph depicts source contributions converging into extraction. This is a bounded, deterministic autonomous workflow. An LLM does not choose the tools, and the agent does not make Gemini requests.

The application persists node states, timestamps and input/output summaries in PostgreSQL. The frontend retrieves those records to show actual execution progress. After completion, selecting a source stage exposes its saved outcome. Restoring history loads the same run; it does not call the external tools again. The recording demonstrates these visible states, while the code establishes the underlying orchestration and persistence mechanisms.

### Extraction, duplicate merging and reference checks

The workflow extracts **30 claims**, normalizes them and merges **12 duplicates**, leaving **18 saved results**. These totals include the external Calendar/Web observations; they are not counts of 18 confirmed event registrations.

Ada's result has status `verified`, duplicate count `1` and no recorded issues. The inspected detail retains both raw email records and their observed evidence. Field checks compare the event, identity, participant status, registration and name with the reference data.

Lindi's result has status `review_required` and the issue codes `inactive_participant` and `name_mismatch`. Sixteen external observations remain flagged for missing event IDs. The selected EVT-101 run target is not inserted into claims that omitted an event identifier. The final distribution is therefore **one verified record and 17 flagged records**.

### Exports, persistence and limits of the evidence

The export buttons request the saved run's CSV endpoint with either all records or `verified_only=true`. The downloaded [full CSV](../exports/eventops-full.csv) has 18 data rows; the [verified-only CSV](../exports/eventops-verified.csv) has one. These row counts were checked after capture. The recording shows the button interactions, while the included files establish the download contents; no operating-system save dialog appears.

The processing workflow completes all 10 stages. Its separate CSV graph node remains **pending** after downloads because the export API does not mutate the recorded execution timeline. This state is preserved in the footage and should not be described as a failed download.

A completed workflow means processing finished, while a verified record means the configured reference checks passed. The demonstration does not prove real-world identity, attendance, unrestricted agent reasoning, sending email, recovery after worker interruption or reliability under production-scale load. It demonstrates one completed production execution against bounded sources and synthetic registration cases.

## Supporting evidence

- [Completed workflow](../screenshots/agent-workflow.png) and [saved result distribution](../screenshots/verification-results.png).
- [Ada verified](../screenshots/ada-verified.png), [retained duplicate evidence](../screenshots/duplicate-evidence.png) and [Lindi conflict](../screenshots/lindi-conflict.png).
- [Restored execution history](../screenshots/execution-history.png) and [recording metadata and checksum](../recordings/manifest.json).
