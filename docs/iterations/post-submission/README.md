# Post-submission evolution

All ongoing development takes place directly in the original v.01 repository on local `main`. Phase 1 was fast-forwarded from the temporary worktree, preserving commits `52b9def` and `5719f7a`. The demonstrated assessment and pre-iteration revisions are preserved by annotated tags; no duplicate application directory is needed. Production configuration, credentials, records and deployment remain unchanged.

- Pre-iteration baseline: `93379eafd445705b0ca678d906031d6f6d0305d5`, annotated tag `pre-iteration-v0.1`.
- Recorded assessment release: `7cc65680950fba53caf302c8fe3a8eadb21b0225`, annotated tag `assessment-demonstrated-v0.1`.
- Checkout: `/Users/keenosmith/Programming/Projects/inference-group/eventops-intelligence-v.01`
- Ongoing branch: `main`. The original feature branch is retained as history.
- Date: 11 October 2026 (Africa/Johannesburg).

## Local review

From this checkout:

```sh
docker compose up -d --wait
cd backend
.venv/bin/python -m app.core.migrate
.venv/bin/python -m app.rag.indexing
GEMINI_ENABLED=false .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 5050
```

In another terminal:

```sh
cd frontend
npm ci
npm run dev
```

Open http://127.0.0.1:5173. Vite proxies to port 5050. PostgreSQL uses the original local configuration (default port 55432), Compose project `eventops-intelligence-v01` and its existing database volume. The original ignored `.env` and credentials are preserved. `.env.example` documents settings for another developer. Create a Python 3.12 `.venv` and install `backend/requirements.lock.txt` if starting from a fresh clone.

See [test evidence](TEST_EVIDENCE.md), [changes](CHANGELOG.md), and [milestone status](ROADMAP.md).

## Future development

Phases 2–6 modify the existing frontend/backend here, with evidence and changes documented in this directory. Do not create another external worktree, application copy or repository. Do not modify the unrelated v.02 project. A push of main may deploy Render and requires explicit owner confirmation. Phase 2 has not begun.
