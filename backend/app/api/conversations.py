from collections.abc import Callable, Iterator
from dataclasses import asdict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.core.demo import session_id
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

from typing import Literal

from app.rag.generation import (
    GroundedAnswer,
    MAX_EVIDENCE,
    generate_grounded_answer,
)

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


class ConversationQuestionRequest(RetrievalRequest):
    generate_answer: bool = False


class ConversationDetailResponse(DomainModel):
    conversation: Conversation
    messages: list[ConversationMessage]


class RetrievalExchangeResponse(DomainModel):
    conversation_id: UUID
    messages: list[ConversationMessage]

    generation_status: Literal[
        "not_requested",
        "generated",
        "insufficient_evidence",
        "unavailable",
    ] = "not_requested"


def get_conversation_repository(request: Request) -> Iterator[ConversationRepository]:
    with connect_db() as connection:
        yield ConversationRepository(connection, session_id(request))


AnswerGenerator = Callable[
    [str, list[dict]],
    GroundedAnswer,
]


def get_answer_generator() -> AnswerGenerator:
    return generate_grounded_answer


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
    payload: ConversationQuestionRequest,
    repository: ConversationRepository = Depends(get_conversation_repository),
    retriever: PostgresSemanticRetriever = Depends(get_rag_retriever),
    answer_generator: AnswerGenerator = Depends(get_answer_generator),
) -> RetrievalExchangeResponse:
    conversation = repository.get_conversation(conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    history = repository.list_messages(conversation_id)

    try:
        resolved = resolve_conversation_question(
            question=payload.question,
            messages=history,
        )

        plan = interpret_query(resolved.retrieval_question)

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    # Retrieve real source evidence from PostgreSQL.
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

    # Generation is explicitly opt-in.
    # Only the five highest-ranked records may
    # be supplied to the generation provider.
    generation_result: GroundedAnswer | None = None

    if payload.generate_answer:
        generation_result = answer_generator(
            plan.query,
            evidence[:MAX_EVIDENCE],
        )

    # Preserve original wording and the decision
    # made during context resolution.
    query_plan = asdict(plan)

    query_plan["context_resolution"] = {
        "used_context": resolved.used_context,
        "inherited_event_id": resolved.inherited_event_id,
    }

    query_plan["generation_status"] = generation_result.status if generation_result else "not_requested"

    try:
        messages = repository.append_retrieval_exchange(
            conversation_id=conversation_id,
            question=resolved.original_question,
            query_plan=query_plan,
            evidence=evidence,
        )

        generation_status = "not_requested"

        if generation_result is not None:
            generation_status = generation_result.status

            if generation_result.status == "generated":
                citations = [
                    citation.model_dump(mode="json")
                    for citation in generation_result.citations
                ]

                try:
                    answer_message = repository.append_generated_answer(
                        conversation_id=conversation_id,
                        answer=generation_result.answer,
                        citations=citations,
                        model=generation_result.model or "",
                    )

                except ValueError:
                    # Reject invalid generated-answer data.
                    # Preserve the valid retrieval exchange.
                    generation_status = "unavailable"
                    repository.set_generation_status(messages[1].id, generation_status)
                    messages[1].query_plan["generation_status"] = generation_status

                else:
                    messages.append(answer_message)

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        ) from exc

    return RetrievalExchangeResponse(
        conversation_id=conversation_id,
        messages=messages,
        generation_status=generation_status,
    )
