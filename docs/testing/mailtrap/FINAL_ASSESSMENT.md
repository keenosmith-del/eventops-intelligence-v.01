# Final controlled Mailtrap assessment

Synthetic assessment registrations use repository directory/events, not personal information. Public Calendar/Web holiday observations remain separate real public-source reads. No authoritative reference is changed.

## Prepared messages

[final-assessment.json](final-assessment.json) contains three individual Sandbox API payloads. Submit each object, not the enclosing array. Plain text bodies:

- [Positive](final-positive.txt): Ada Mensah / ada.mensah@example.com / EVT-101, active P-001. Expected verified.
- [Duplicate](final-duplicate.txt): same Ada fields; expected one merged registration, duplicate_count 1, both message references.
- [Inactive conflict](final-inactive-conflict.txt): lindi.mokoena@example.com / EVT-101, authoritative P-003 is inactive. Claimed name Lindi Mokoena-Test differs from Lindi Mokoena; expected inactive_participant and name_mismatch, never verified.

Uppercase email/lowercase event exercise normalization. Directory and events.csv supply actual identities and AI Engineering Summit reference.

## Exact manual submission

1. Mailtrap → **Sandboxes** → **My Project** → **My Sandbox**, ID **4953522**, account 2853336. Do not select transactional API/SMTP or forwarding.
2. **Integration → SMTP**, choose the Python smtplib code sample. Use **sandbox.smtp.mailtrap.io**, port **2525**, existing username/password. Do not reset credentials or create wider permissions. Keep credentials out of chat/screenshots/Git.
3. Use each prepared subject/text exactly, with synthetic sender registration@example.com and recipient reviewer@example.com. Send positive, duplicate and inactive-conflict **once each** using the owner's authorized testing integration. Sandbox capture does not deliver to real recipients.
4. Refresh; confirm all three subjects start `EventOps final assessment | EVT-101 |`. Keep these as the newest three before the bounded verification. Notify Codex when ready.
5. Production Agent Workspace → EVT-101 → Records per source 5 → Run verification once. Inspect the real email API evidence and merged/flagged results. The app stays read-only; no sending integration is added.

An already-authorized sandbox-send API credential can use `POST https://sandbox.api.mailtrap.io/api/send/4953522`, one JSON object per request. `scripts/prepare-mailtrap-assessment.py --submit` fixes this endpoint/ID and stops on the first unconfirmed result, without retries. **The existing local application's token returned HTTP 401 on insertion attempt one; zero messages were submitted. Do not repeat with that token.** Manual SMTP uses the owner's existing integration. No credential expansion is requested.

Never use send.api.mailtrap.io, bulk delivery, real recipients or forwarding. No inbox cleanup. Owner submission is complete. Do not resend. Production run `ef50214e-9ec1-4903-a80c-ada28ca7d5cb` retrieved all three messages, verified Ada against P-001/EVT-101, merged her duplicate with both message references, and flagged Lindi against inactive P-003 with a name mismatch. See the production acceptance report for actual saved outcomes and CSV/replay checks.

References: [Sandbox send API](https://docs.mailtrap.io/developers/email-sandbox/send-test-emails), [Sandbox integration](https://docs.mailtrap.io/email-sandbox/setup/sandbox-api-integration).

The standalone owner-operated sender is `python3 scripts/send_mailtrap_tests.py`; `--start-at 2` skips message 1 entirely. It prompts for credentials without storing them, spaces submissions 11 seconds apart, and stops on an error without retrying. It was used successfully; no further sending is needed.
