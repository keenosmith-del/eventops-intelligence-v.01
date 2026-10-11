# Bounded verification agent

`workflow.py` builds a LangGraph StateGraph:

Trigger → Calendar → Email → Web → Extraction → Normalization → Deduplication → Verification → Discrepancy handling → Persistence.

The tools are deliberately executed sequentially to bound concurrency and make each failure observable. Each node independently records pending/running/completed/failed/skipped state and safe inputs/outputs in PostgreSQL. This is a deterministic autonomous read/verify workflow, not LLM-driven tool selection or an open-ended reasoning loop. It makes no Gemini requests.

- Calendar reads an actual public remote iCalendar feed using the `icalendar` parser.
- Email reads a configured Mailtrap Email Testing sandbox's message list and at most 3 plain-text bodies over HTTPS. It never sends mail.
- Web reads JSON reference data or extracts visible text from HTML over HTTPS.
- Source errors and missing connections are retained. A missing tool yields a partial run, not a successful full integration claim.
- Regex-based extraction recognizes explicit EVT IDs, addresses and `Name:`/`Full name:` labels. JSON supports `event_id`, `full_name`, `email`, `title`, `starts_at`, `venue`; the default holiday API maps `name` and `date`. Calendar extracts summary, description, UID, start and location. Ambiguous references remain flagged rather than guessed.
- Unicode/whitespace/email/date normalization precedes deterministic deduplication. Exact duplicate evidence is retained; conflicting fields are flagged.
- Verification compares against current indexed PostgreSQL event/directory records. Inactive or unregistered people cannot be verified. Run target IDs are never injected into missing source claims.
- CSV export is an explicit API operation after persistence; it has a durable observed export step.

API routes: `GET /api/agents/connections`, `POST/GET /api/agents/runs`, `GET /api/agents/runs/{uuid}`, `/results` and `/export.csv`. Inputs are event_id and max_records only; callers cannot choose arbitrary URLs. Configuration lives server-side. See [deployment guide](../../../docs/deployment/README.md).

FastAPI BackgroundTasks is not a resumable queue. Interrupted runs are marked failed on read after ten minutes; restarting a worker does not replay external tools. PostgreSQL records remain auditable. Tests inject explicitly named adapters or mocked HTTPS transports; production adapters never fall back to fixtures.


Part 2 adds actual per-source parsed counts and field comparison decisions/reference fields to saved stage/result outputs. Final persistence-step completion and terminal run status are committed atomically. Runs now record `execution_mode`: production `real_https_read_only`, explicit controlled adapters `controlled_adapter_test`, assessment fixtures `controlled_assessment_fixture`, or the bounded actual email probe `real_mailtrap_read_only_probe`. No API flag enables fixture replacement. Older runs may lack this metadata.

The frontend replays saved step timestamps without invoking LangGraph. Protected service orchestration is documented in [n8n setup](../../../automations/n8n/README.md); no n8n runtime execution has been verified.
