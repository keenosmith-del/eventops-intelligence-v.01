# EventOps Intelligence — Backend

Python backend for EventOps Intelligence, an AI-powered
event operations and workflow automation platform.

## Technology

- Python 3.12
- FastAPI
- Pydantic
- Uvicorn
- HTTPX
- pytest

Planned integrations include Gemini, LangGraph, n8n,
Google Calendar, Gmail, and PostgreSQL.

## Current Implementation

The initial FastAPI application is operational.

Implemented:

- FastAPI application initialization
- Service health endpoint
- Automatically generated OpenAPI documentation
- Automated health endpoint test

### API Endpoints

| Method | Endpoint      | Description                   |
| ------ | ------------- | ----------------------------- |
| GET    | /health       | Application process health    |
| GET    | /docs         | Interactive API documentation |
| GET    | /openapi.json | OpenAPI specification         |

The health endpoint confirms that the API process
is responding. It does not yet validate external
dependencies or database connectivity.

## Local Development

From the backend directory:

### Activate virtual environment

```bash
source .venv/bin/activate
```

### Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Start development server

```bash
python -m uvicorn app.main:app --reload --reload-dir app --host 127.0.0.1 --port 5050
```

API: http://127.0.0.1:5050

Swagger: http://127.0.0.1:5050/docs

### Run tests

```bash
python -m pytest -q
```

## Architecture

The backend will progressively introduce modules
for the following responsibilities:

- `api/` — HTTP routes and request handling
- `models/` — Data contracts and validation schemas
- `services/` — Application-level business logic
- `rag/` — Document ingestion and semantic retrieval
- `agents/` — LangGraph agent orchestration
- `integrations/` — External API integrations
- `verification/` — Data validation and reconciliation
- `core/` — Configuration and shared infrastructure

## Engineering Principles

- Typed request and response contracts
- Separation of application responsibilities
- Deterministic verification of authoritative data
- Evidence-grounded AI outputs
- Explicit error handling
- Durable state for production
- Reproducible development environments
- Automated testing

## Deployment

Target: Python web service on Render.

Persistent state will be stored in PostgreSQL
rather than relying on local process memory.

Production configuration and deployment procedures
will be documented as implementation progresses.
