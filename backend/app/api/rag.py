from collections.abc import Iterator
from dataclasses import asdict
from functools import lru_cache
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field

from app.core.database import connect_db
from app.models.domain import DomainModel
from app.rag.embeddings import LocalEmbeddingModel
from app.rag.postgres_retrieval import PostgresSemanticRetriever
from app.rag.query import interpret_query

router = APIRouter(
    prefix="/api/rag",
    tags=["RAG"],
)


# TypedDict for the state of the workflow. Each node in the workflow graph takes a State and returns a State.
class RetrievalRequest(DomainModel):
    question: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)


class QueryPlanResponse(DomainModel):
    query: str
    event_id: str | None = None
    record_type: str | None = None
    participant_status: str | None = None
    policy_category: str | None = None


class EvidenceResponse(DomainModel):
    document_id: str
    record_id: str
    record_type: str
    event_id: str | None
    content: str
    score: float
    source_reference: str
    metadata: dict[str, str]


class RetrievalResponse(DomainModel):
    question: str
    query_plan: QueryPlanResponse
    evidence_count: int
    evidence: list[EvidenceResponse]


_embedding_initialization_lock = Lock()


# Get the cached embedding model instance.
@lru_cache(maxsize=1)
def _cached_embedding_model() -> LocalEmbeddingModel:
    return LocalEmbeddingModel()


# Get the embedding model instance, ensuring that it is initialized only once even under concurrent requests.
def get_embedding_model() -> LocalEmbeddingModel:
    # lru_cache alone can initialize twice when concurrent first requests arrive.
    with _embedding_initialization_lock:
        return _cached_embedding_model()


# Get a PostgresSemanticRetriever instance for the current request, using the cached embedding model.
def get_rag_retriever() -> Iterator[PostgresSemanticRetriever]:
    with connect_db() as connection:
        yield PostgresSemanticRetriever(
            connection=connection,
            embedding_model=get_embedding_model(),
        )


# Retrieve evidence for a given question using the RAG retriever. Returns a structured response containing the question, query plan, and retrieved evidence.
@router.post(
    "/retrieve",
    response_model=RetrievalResponse,
)
def retrieve_evidence(
    payload: RetrievalRequest,
    retriever: PostgresSemanticRetriever = Depends(get_rag_retriever),
) -> RetrievalResponse:

    try:
        plan = interpret_query(payload.question)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    hits = retriever.search(
        query=plan.query,
        top_k=payload.top_k,
        record_type=plan.record_type,
        event_id=plan.event_id,
        participant_status=plan.participant_status,
        policy_category=plan.policy_category,
    )

    evidence = [
        EvidenceResponse(
            document_id=hit.record.document_id,
            record_id=hit.record.record_id,
            record_type=hit.record.metadata["record_type"],
            event_id=hit.record.event_id,
            content=hit.record.content,
            score=hit.score,
            source_reference=(hit.record.metadata["source_reference"]),
            metadata=hit.record.metadata,
        )
        for hit in hits
    ]

    return RetrievalResponse(
        question=payload.question,
        query_plan=QueryPlanResponse(**asdict(plan)),
        evidence_count=len(evidence),
        evidence=evidence,
    )
