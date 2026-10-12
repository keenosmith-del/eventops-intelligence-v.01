from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.models.domain import DomainModel


# Conversation and ConversationMessage models for managing conversation data.
class Conversation(DomainModel):
    id: UUID
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )
    created_at: datetime
    updated_at: datetime


# ConversationMessage model for individual messages within a conversation.
class ConversationMessage(DomainModel):
    id: int = Field(gt=0)
    conversation_id: UUID

    role: Literal["user", "assistant"]
    kind: Literal["question", "retrieval", "answer"]

    content: str = Field(min_length=1)

    query_plan: dict[str, Any] | None = None
    evidence: list[dict[str, Any]] = Field(default_factory=list)

    created_at: datetime

    @model_validator(mode="after")
    def validate_message_type(self):
        if self.role == "user" and self.kind != "question":
            raise ValueError("User messages must have kind 'question'")

        if self.role == "assistant" and self.kind == "question":
            raise ValueError("Assistant messages cannot have kind 'question'")

        return self
