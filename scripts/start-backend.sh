#!/usr/bin/env bash
set -euo pipefail
TASK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$TASK_ROOT/backend"
export EMBEDDING_THREADS="${EMBEDDING_THREADS:-1}"
export TOKENIZERS_PARALLELISM=false
export LANGSMITH_TRACING=false
python -m app.core.migrate
python -m app.rag.indexing
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-5050}" --workers 1
