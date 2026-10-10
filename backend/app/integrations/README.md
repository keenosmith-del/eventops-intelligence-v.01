# Read-only HTTPS integrations

`tools.py` implements real remote iCalendar, Web JSON/HTML and Mailtrap Email Testing message/body readers. Public configuration is reported as `configured`; only executed step records establish successful connectivity.

Default sources:

- [Office Holidays South Africa subscription](https://www.officeholidays.com/subscribe/south-africa): actual HTTPS iCalendar feed.
- [Nager.Date public holiday API](https://date.nager.at/api/v3/PublicHolidays/2026/ZA): actual 2026 ZA reference records.

These public holiday sources do not claim to describe the fictional EVT assessment records. Missing EVT references remain discrepancies.

Set `CALENDAR_FEED_URL` / `WEB_SOURCE_URL` to other public HTTPS sources, or blank to disable. URLs with credentials, non-HTTPS schemes, private/local DNS answers or non-standard ports are rejected. No redirects or retries are followed. Sources are read with 12-second timeouts and a 512 KB decoded read bound. URL query strings are omitted from displayed source references to avoid exposing access parameters. Source URLs are controlled by the server owner, not by public requests.

For Mailtrap configure `MAILTRAP_API_TOKEN`, numeric `MAILTRAP_ACCOUNT_ID` and `MAILTRAP_INBOX_ID`. Only a dedicated synthetic-data sandbox is supported. The real message-list/body API contract is exercised with mocked transport in tests; no live email connection has been exercised because credentials are absent. No public sending endpoint or SMTP dependency exists.
