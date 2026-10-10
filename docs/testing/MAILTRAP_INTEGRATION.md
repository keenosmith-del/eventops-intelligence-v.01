# Controlled Mailtrap integration verification

## Connection confirmed, inbox empty

On 2026-10-10 the existing `app.integrations.tools.read_email(1)` reached the real HTTPS API for account **2853336**, sandbox **4953522**: **HTTP 200, zero messages**. No token, headers or provider response body were printed. No email was sent during this check. The token remains in the project-root `.env`.

FastAPI's `app/main.py` loads the **project-root** `.env` with `override=False`. The adapter reads `MAILTRAP_API_TOKEN`, `MAILTRAP_ACCOUNT_ID` and `MAILTRAP_INBOX_ID` from the server process environment. Mailtrap calls its sandbox identifier an inbox ID in the API. Standalone commands must load the root `.env`, as the test below does. Restart an already-running backend after changing credentials; existing process environment values take precedence over `.env`.

The adapter makes GET requests to:

- `https://mailtrap.io/api/accounts/{account_id}/inboxes/{inbox_id}/messages`
- `https://mailtrap.io/api/accounts/{account_id}/inboxes/{inbox_id}/messages/{message_id}/body.txt`

Authentication uses the `Api-Token` header. TLS verification is enabled; redirects and retries are disabled. Each response is bounded to 512 KB; body text retained by the adapter is at most 10,000 characters. The normal adapter reads at most three message bodies; the controlled test below requests **one**.

HTTP 200 with `[]` is a successful empty read (`messages: []`), not a connection failure. Missing credentials raise `NotConnected`; non-success HTTP status, DNS/timeout and invalid message payloads raise `ToolError`. In the graph, an empty read completes the Email step with `messages_read: 0`; a connection failure fails the step, and missing configuration skips it. Configuration status alone does not prove connectivity. Unit tests cover empty, 401, 403, 503, timeout and malformed responses separately.

## Synthetic message and expected outcome

Use [the complete Sandbox API payload](mailtrap/evt101-registration.json) and [plain-text body](mailtrap/evt101-registration.txt). Subject:

`EventOps controlled verification | EVT-101 | MAILTRAP-EVT101-001`

All identities and addresses are assessment-only examples. The message deliberately uses:

| Input | Normalized / verified expectation |
| --- | --- |
| `evt-101` | `EVT-101`; event reference found |
| Uppercase participant email | `lindi.mokoena@example.com`; participant `P-003` found |
| `Lindi   Mokoena-Test` | `Lindi Mokoena-Test`; differs from directory name `Lindi Mokoena` |
| Submitter claims active status | Actual directory participant is inactive |

Expected result: **one `review_required` record**, `name_mismatch` and `inactive_participant`, with references `EVT-101` and `P-003`, plus the actual Mailtrap message ID/body URL as provenance. The verifier checks authoritative directory status; it does not parse the prose status assertion as a separate structured field. The incorrect name is retained rather than silently repaired. An offline unit test confirms this expectation against the repository's actual structured reference files; this is not proof of live ingestion.

## Insert using Mailtrap Email Sandbox

Open Mailtrap → Email Sandbox → the dedicated sandbox **4953522**. Its integration/testing controls expose the Sandbox API sample. Use the JSON payload above with the Sandbox **Send Test Emails** endpoint `POST https://sandbox.api.mailtrap.io/api/send/4953522` and your token's sandbox send permission. This endpoint captures the email in the selected testing inbox. See the official [Send Test Emails API](https://docs.mailtrap.io/developers/email-sandbox/send-test-emails) and [Sandbox API integration guide](https://docs.mailtrap.io/email-sandbox/setup/sandbox-api-integration).

Alternatively, deliberately run this once from the **repository root**. It inserts only the prepared synthetic message into the fixed sandbox. The application adapter remains read-only. This command has **not** been executed by Codex.

```bash
backend/.venv/bin/python - <<'PY'
import json
import os
from pathlib import Path
import httpx
from dotenv import load_dotenv

root = Path.cwd()
load_dotenv(root / '.env', override=False)
if (os.getenv('MAILTRAP_ACCOUNT_ID'), os.getenv('MAILTRAP_INBOX_ID')) != ('2853336', '4953522'):
    raise SystemExit('Configured IDs do not match the controlled sandbox.')
token = os.getenv('MAILTRAP_API_TOKEN')
if not token:
    raise SystemExit('Server-side Mailtrap token is missing.')
payload = json.loads((root / 'docs/testing/mailtrap/evt101-registration.json').read_text())
try:
    with httpx.Client(timeout=httpx.Timeout(12, connect=5), follow_redirects=False) as client:
        response = client.post(
            'https://sandbox.api.mailtrap.io/api/send/4953522',
            headers={'Api-Token': token}, json=payload,
        )
    if response.status_code != 200:
        raise SystemExit(f'Sandbox insertion returned HTTP {response.status_code}; no retry made.')
    if response.json().get('success') is not True:
        raise SystemExit('Sandbox API did not confirm insertion; check the inbox before retrying.')
except (httpx.HTTPError, ValueError):
    raise SystemExit('Sandbox insertion failed or could not be confirmed; check inbox before retrying.') from None
print('Sandbox API confirmed insertion. Open sandbox 4953522 to inspect the message.')
PY
```

A read-capable token may lack send permission. If insertion returns 401/403, use the sandbox's authorized testing integration or adjust that token's sandbox permissions server-side. Keep the token out of shell arguments, screenshots and logs. Insert this email as the newest message immediately before the test; the probe does not scan unrelated messages or clean the inbox.

## Single bounded live integration test

From the repository root, with PostgreSQL running, migrations applied and the existing assessment references indexed:

```bash
cd backend
RUN_MAILTRAP_LIVE=true GEMINI_ENABLED=false .venv/bin/python -m pytest \
  tests/test_mailtrap_live.py -q -s -rs --tb=no
```

This one opt-in test performs at most **two real GETs** (list + newest message body), no retries, one record, no email sending and no Gemini request. It then executes the existing LangGraph extraction → normalization → deduplication → verification → discrepancy → PostgreSQL persistence stages using the fetched payload and actual indexed database references. Calendar and Web are explicitly skipped for this email-only probe, so the retained run truthfully has status **`partial`**, not full three-tool completion. CSV export is explicitly skipped.

The test checks normalized fields, both discrepancy codes, reference IDs, actual message provenance, completed stages and a second database reload. It prints only the retained execution UUID. Runs/results/steps are deliberately retained for review, including failed verification assertions. It does not alter reference data. In local `DEMO_MODE=false`, inspect `/agents/runs/{UUID}` or Execution History. The probe creates an unowned local run; public demo sessions cannot access it. For a session-owned three-tool run, use the existing Agent Workspace after insertion.

Without `RUN_MAILTRAP_LIVE=true`, the test skips without network access. With an empty connected inbox, it skips with an explicit empty-inbox reason and creates no execution. A connection error fails the opted-in test; it is never reported as an empty inbox. A different newest subject fails before creating a run. No synthetic message is injected as a fallback. The limits bound request count, response size and per-request timeouts; they are not a hard whole-test deadline across DNS and database work.

Current live evidence: **connection succeeded; inbox empty; message-processing/persistence test is pending insertion**. After insertion, rerun only this test and retain its printed UUID as the live execution evidence.
