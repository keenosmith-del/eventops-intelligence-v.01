from fastapi import FastAPI

from app.api.rag import router as rag_router

app = FastAPI(
    title="EventOps Intelligence API",
    description="AI-powered event operations, RAG and agentic workflow platform.",
    version="0.1.0",
)

app.include_router(rag_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "eventops-intelligence-api"}
