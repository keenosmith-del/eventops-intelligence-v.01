# Protected n8n verification handoff

The repository contains an inactive workflow export, `eventops-verification.json`. No n8n executable or running n8n container was present during the local audit. Its import, credential binding and actual webhook execution remain unverified. Do not describe it as connected based on this JSON.

The workflow delegates verification to the existing LangGraph backend. It submits one delivery, waits two seconds between status reads (at most 30 reads), and returns the persisted terminal run. It validates the returned ID/status. Failed runs return HTTP 502; partial outcomes remain explicitly partial. The workflow timeout is 180 seconds. HTTP/network failures terminate; no automatic POST retries or algorithm duplication occur.

## Configure and validate

1. Apply migrations with `cd backend && .venv/bin/python -m app.core.migrate`. Migration `004_n8n_triggers.sql` stores idempotent delivery keys and run IDs.
2. Set a random server-only `N8N_SERVICE_TOKEN` of at least 32 characters in the root `.env`; restart FastAPI. Never put this value in Vite variables, workflow JSON, screenshots or browser requests. The default service quota is `N8N_DAILY_RUN_LIMIT=10`, also bounded by the existing global agent quota and concurrent-run admission.
3. Import the JSON into your own local n8n instance, leaving it inactive until credentials are bound. Node compatibility/import has not been tested in an n8n runtime.
4. Create an n8n Header Auth credential named **EventOps backend service key (configure)**: header `X-EventOps-Service-Key`, value matching the backend token. Bind it to Start verification and Read saved execution.
5. Create a separate Header Auth credential for **EventOps webhook caller key (configure)**. Choose a caller header/key distinct from the backend credential and bind it to Protected trigger. Callers need only this inbound credential.
6. Set both HTTP nodes to the actual private backend origin reachable from n8n. The export uses `http://host.docker.internal:5050` for a local Docker-on-macOS setup; confirm reachability for your network. Do not make the service publicly reachable just to accommodate this example.
7. Keep `GEMINI_ENABLED=false`. Use n8n's authenticated test webhook first, supplying the following body and the inbound credential header. The UUID below is illustrative; generate a fresh UUID for each intended new execution, retaining it for retries.

```json
{"idempotency_key":"e6bf642e-909e-4fb6-9379-53db64b6e721","event_id":"EVT-101","max_records":10}
```

8. Record the actual response run ID, status, tool outcomes, timestamps and saved result counts. Repeat the same delivery: it must return the same ID without a second run. Changed inputs with that key must return HTTP 409. Missing/wrong service credentials return 401; unconfigured service returns 503. Check the protected GET directly when a polling/network timeout leaves the outcome uncertain. Do not start a new delivery merely to recover a response.
9. Activate the production webhook only after this test passes. Record an actual execution reference before describing n8n as executed or adding a UI integration indicator.

## Backend contracts and boundaries

- `POST /api/integrations/n8n/runs`: protected service header, body above; HTTP 202 with `id`, `status`, `event_id`, `reused`, `origin`.
- `GET /api/integrations/n8n/runs/{id}`: same credential; full persisted service execution. Unrelated reviewer runs return 404.
- Service-triggered runs have no browser reviewer-session owner. Public reviewer history cannot restore them; local shared mode remains the existing behavior. The Agent Workspace deliberately has no n8n connected/executed indicator.
- Reviewer tokens cannot authorize these endpoints. Services cannot choose arbitrary source URLs. Source adapters remain bounded, read-only HTTPS calls; LangGraph persists results in PostgreSQL.
- Successful/error execution-data saving is disabled in the export to avoid retaining inbound headers unnecessarily. Apply your n8n instance's access/retention controls; never include credentials in recorded evidence.
- FastAPI BackgroundTasks is not a durable queue. Delivery idempotency prevents duplicate creation, but does not resume an interrupted run.

PostgreSQL-backed tests verify authentication, quota use, session isolation, concurrency/idempotency, real LangGraph persistence with explicitly synthetic test adapters, and workflow structure. They do **not** verify n8n runtime import or external webhook execution.

Official setup references: [Webhook authentication](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/) and [HTTP Request credentials](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/).
