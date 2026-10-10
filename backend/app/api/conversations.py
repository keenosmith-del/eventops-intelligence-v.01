from collections.abc import Iterator
from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field

from app.api.rag import (
    EvidenceResponse,
    RetrievalRequest,
    get_rag_retriever,
)
from app.core.database import connect_db
from app.models.conversation import Conversation, ConversationMessage
from app.models.domain import DomainModel
from app.rag.context import resolve_conversation_question
from app.rag.postgres_retrieval import PostgresSemanticRetriever
from app.rag.query import interpret_query
from app.services.conversation_repository import ConversationRepository

router = APIRouter(
    prefix="/api/conversations",
    tags=["RAG Conversations"],
)


class CreateConversationRequest(DomainModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )


class ConversationDetailResponse(DomainModel):
    conversation: Conversation
    messages: list[ConversationMessage]


class RetrievalExchangeResponse(DomainModel):
    conversation_id: UUID
    messages: list[ConversationMessage]


def get_conversation_repository() -> Iterator[ConversationRepository]:
    with connect_db() as connection:
        yield ConversationRepository(connection)


@router.post(
    "",
    response_model=Conversation,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    payload: CreateConversationRequest,
    repository: ConversationRepository = Depends(get_conversation_repository),
) -> Conversation:
    return repository.create_conversation(title=payload.title)


@router.get(
    "",
    response_model=list[Conversation],
)
def list_conversations(
    limit: int = 20,
    repository: ConversationRepository = Depends(get_conversation_repository),
) -> list[Conversation]:
    if not 1 <= limit <= 100:
        raise HTTPException(
            status_code=422,
            detail="Limit must be between 1 and 100",
        )

    return repository.list_recent_conversations(limit=limit)


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailResponse,
)
def get_conversation(
    conversation_id: UUID,
    repository: ConversationRepository = Depends(get_conversation_repository),
) -> ConversationDetailResponse:
    conversation = repository.get_conversation(conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    messages = repository.list_messages(conversation_id)

    return ConversationDetailResponse(
        conversation=conversation,
        messages=messages,
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=RetrievalExchangeResponse,
)
def submit_question(
    conversation_id: UUID,
    payload: RetrievalRequest,
    repository: ConversationRepository = Depends(get_conversation_repository),
    retriever: PostgresSemanticRetriever = Depends(get_rag_retriever),
) -> RetrievalExchangeResponse:
    conversation = repository.get_conversation(conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    # Retrieve the persisted history for this conversation.
    history = repository.list_messages(conversation_id)

    try:
        # Resolve references such as "its" and "that event".
        resolved = resolve_conversation_question(
            question=payload.question,
            messages=history,
        )

        # Interpret the resolved question using our
        # existing deterministic query planner.
        plan = interpret_query(resolved.retrieval_question)

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
        ).model_dump(mode="json")
        for hit in hits
    ]

    # Preserve both the interpreted query plan and
    # the context-resolution decision.
    query_plan = asdict(plan)

    query_plan["context_resolution"] = {
        "used_context": resolved.used_context,
        "inherited_event_id": resolved.inherited_event_id,
    }

    try:
        messages = repository.append_retrieval_exchange(
            conversation_id=conversation_id,
            question=resolved.original_question,
            query_plan=query_plan,
            evidence=evidence,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        ) from exc

    return RetrievalExchangeResponse(
        conversation_id=conversation_id,
        messages=messages,
    )
