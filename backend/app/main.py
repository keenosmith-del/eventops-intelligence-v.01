import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import TypeAdapter, ValidationError
from starlette.concurrency import run_in_threadpool

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

from app.api.agents import router as agents_router
from app.api.conversations import router as conversations_router
from app.api.knowledge import router as knowledge_router
from app.api.n8n import require_service
from app.api.n8n import router as n8n_router
from app.api.rag import router as rag_router
from app.core.demo import (
    consume_budget,
    demo_enabled,
    identify_session,
)
from app.core.demo import (
    router as demo_router,
)

app = FastAPI(
    title="EventOps Intelligence API",
    description="Evidence-grounded event operations and bounded verification tooling.",
    version="0.1.0",
)
for router in [
    rag_router,
    conversations_router,
    agents_router,
    knowledge_router,
    demo_router,
    n8n_router,
]:
    app.include_router(router)


@app.middleware("http")
async def public_demo_guard(request: Request, call_next):
    if request.method == "OPTIONS" or not request.url.path.startswith("/api/"):
        return await call_next(request)
    try:
        if request.method == "POST":
            length = request.headers.get("content-length", "0")
            if not length.isdigit() or int(length) > 16000:
                raise HTTPException(413, "Request exceeds the 16 KB limit.")
            if len(await request.body()) > 16000:
                raise HTTPException(413, "Request exceeds the 16 KB limit.")
        service_request = request.url.path.startswith("/api/integrations/n8n/")
        if service_request:
            await run_in_threadpool(require_service, request)
        if not service_request and demo_enabled() and request.url.path != "/api/demo/session":
            owner = await run_in_threadpool(
                identify_session, request.headers.get("x-demo-session")
            )
            request.state.demo_session_id = owner
            await run_in_threadpool(
                consume_budget,
                f"session:{owner}",
                int(os.getenv("DEMO_REQUEST_LIMIT", "2000")),
            )
            if request.method == "POST" and request.url.path.endswith("/messages"):
                payload = await request.json()
                requested = False
                if isinstance(payload, dict):
                    try:
                        requested = TypeAdapter(bool).validate_python(
                            payload.get("generate_answer", False)
                        )
                    except ValidationError:
                        pass  # The request model returns the validation error.
                if requested:
                    await run_in_threadpool(
                        consume_budget,
                        "generation",
                        int(os.getenv("GEMINI_DAILY_LIMIT", "10")),
                    )
            if request.method == "POST":
                await run_in_threadpool(
                    consume_budget,
                    "public_writes",
                    int(os.getenv("DEMO_WRITE_LIMIT", "100")),
                )
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response
    except HTTPException as exc:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    except Exception:
        return JSONResponse(
            {
                "detail": "The backend could not complete this request. Check database availability."
            },
            status_code=503,
        )


origins = [
    x.strip().rstrip("/")
    for x in os.getenv("FRONTEND_ORIGINS", "").split(",")
    if x.strip()
]
if os.getenv("APP_ENV") == "production" and not demo_enabled():
    raise RuntimeError("Production assessment access requires DEMO_MODE=true.")
if "*" in origins:
    raise RuntimeError(
        "FRONTEND_ORIGINS must contain explicit trusted origins, not a wildcard."
    )
if demo_enabled() and not origins:
    raise RuntimeError("Public DEMO_MODE requires explicit FRONTEND_ORIGINS.")
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Demo-Session"],
        expose_headers=["Content-Disposition"],
    )


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "eventops-intelligence-api"}
