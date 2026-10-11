# EventOps Intelligence — Part 1: RAG Demonstration

**Recording:** [eventops-rag-demonstration.mp4](../recordings/eventops-rag-demonstration.mp4)  
**Duration:** 1 minute 10.50 seconds  
**Application:** [EventOps Intelligence](https://eventops-intelligence.onrender.com)  
**Capture:** 11 October 2026 · production release `7cc6568`  
**Format:** Silent H.264 MP4 · 1920 × 1080 · 30 fps

## Non-technical explanation

This recording shows how a reviewer can find a specific event rule using ordinary language, inspect the source behind it and continue the conversation without repeating the event identifier.

The reviewer asks, **“What time does check-in close for EVT-101?”** The Knowledge Assistant retrieves **POL-003**, an event policy stating that check-in closes at **08:45 South Africa Standard Time**. The policy is opened in the evidence panel so viewers can read the rule and see where it came from. This makes the deadline traceable rather than asking the reviewer to accept an unsupported statement.

The reviewer follows with **“What time does its check-in close?”** Although this question omits EVT-101, the application carries that event forward from the preceding exchange. The Context tab shows the inherited event and confirms that conversation context was used. This demonstrates a practical follow-up: a reviewer can refer to an event already being discussed while still checking which event the system understood.

The reviewer then starts a new chat and opens the earlier conversation from the sidebar history. Its saved exchanges and source evidence are restored, allowing the reviewer to return to the information later.

The visible **“Evidence only · AI generation was not requested”** label is central to interpreting this recording. It shows a successful evidence lookup, not a newly generated Gemini answer. The deadline comes from the displayed policy itself. The benefit demonstrated is access to relevant, inspectable event information with continuity between questions and a saved record of the conversation.

## Technical explanation

### What is visibly demonstrated

| Interaction | Evidence shown | Capability demonstrated |
| --- | --- | --- |
| Question containing EVT-101 | Relevant POL-003 policy | Event-aware retrieval |
| Expanded evidence disclosure | Policy text, document and source reference | Source traceability |
| Follow-up using “its” | Context carried forward as EVT-101 | Context resolution |
| Context tab | Inherited event, context use and retrieval question | Inspectable query context |
| New chat followed by history selection | Saved exchanges and retrieved evidence | Conversation persistence and restoration |

POL-003 identifies `policies.csv` as its document and `data/structured/policies.csv#policy_id=POL-003` as its source reference. The policy's wording supports the 08:45 deadline directly. Its similarity score describes retrieval relevance; it is not a calibrated probability that a claim is true.

### Implementation supporting the behavior

The application sends questions through `POST /api/conversations/{id}/messages`. Its implementation resolves supported contextual references, interprets the retrieval question and searches the indexed knowledge records using local embeddings and PostgreSQL/pgvector cosine-distance ranking. Event and policy filters constrain eligible evidence before the results are returned.

For the follow-up, the deterministic context resolver reads ordered messages from the stored conversation. It associates the supported reference “its” with an unambiguous prior event and preserves the original question. The inherited event and context-use metadata are saved with the retrieval response and exposed through the Context panel. This behavior does not require a Gemini call.

The frontend lists saved conversations and restores their details through the conversation API. Returning to an earlier conversation loads its persisted messages and evidence; it is not a demonstration of regenerating an answer or rerunning the original question. The recording shows the resulting user experience, while the repository implementation supplies the explanation of the underlying database and retrieval mechanisms.

### Generation status and scope

RAG means retrieval-augmented generation, but retrieval and generation are separable stages in this application. These requests keep `generate_answer=false`, and the response status is `not_requested`. No new Gemini response or billable generation request is demonstrated. Previous Gemini verification is outside this recording's evidence.

This example establishes successful retrieval and context handling for an EVT-101 check-in question. It does not establish unrestricted conversational reasoning, general pronoun resolution, factual accuracy for every possible question or generated-answer grounding. The history interaction demonstrates restoration within the same reviewer session; it does not demonstrate access across separate isolated reviewer sessions.

## Supporting evidence

- [Knowledge Assistant screenshot with POL-003 expanded](../screenshots/knowledge-assistant.png).
- [Recording metadata and checksum](../recordings/manifest.json).
- [Complete walkthrough](../recordings/eventops-complete-walkthrough.mp4), which places this focused excerpt within the full reviewer journey.
