# Post-submission evolution

This iteration extends the assessed v.01 application in a separate checkout and database. Main remains the submitted baseline. No production configuration, records, migrations, or deployment are changed.

- Baseline: `93379eafd445705b0ca678d906031d6f6d0305d5` (local main and origin/main agree).
- Checkout: `/Users/keenosmith/Programming/Projects/inference-group/eventops-intelligence-next-iteration`
- Branch: `feature/post-submission-evolution`
- Date: 11 October 2026 (Africa/Johannesburg).

## Local review

From this checkout:

```sh
docker compose up -d --wait
cd backend
.venv/bin/python -m app.core.migrate
.venv/bin/python -m app.rag.indexing
GEMINI_ENABLED=false .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 5051
```

In another terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5174. Vite proxies to port 5051. PostgreSQL uses port 55433, database `eventops_next`, Compose project `eventops-next-iteration`, volume `eventops-next-iteration_postgres_data`. A new ignored `.env` contains freshly generated local credentials; no production credentials were copied. `.env.example` documents settings for another developer. Create a Python 3.12 `.venv` and install `backend/requirements.lock.txt` if starting from a fresh clone.

See [test evidence](TEST_EVIDENCE.md), [changes](CHANGELOG.md), and [milestone status](ROADMAP.md).
