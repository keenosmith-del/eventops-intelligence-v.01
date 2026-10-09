
from fastapi import FastAPI

app = FastAPI(
    title="EventOps Intelligence API",
    description="AI-powered event operations, RAG and agentic workflow platform.",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "eventops-intelligence-api"
    }
