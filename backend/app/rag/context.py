import re

from collections.abc import Sequence
from dataclasses import dataclass

from app.models.conversation import ConversationMessage

EVENT_ID_PATTERN = re.compile(
    r"\bEVT-\d+\b",
    re.IGNORECASE,
)

CONTEXT_REFERENCE_PATTERN = re.compile(
    r"\b(?:its|that event|this event|the same event)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ResolvedConversationQuestion:
    original_question: str
    retrieval_question: str
    inherited_event_id: str | None = None

    @property
    def used_context(self) -> bool:
        return self.inherited_event_id is not None


def resolve_conversation_question(
    question: str,
    messages: Sequence[ConversationMessage],
) -> ResolvedConversationQuestion:
    """
    Resolve clear event references using persisted history.

    Explicit event identifiers always take precedence.

    Ambiguous references fail instead of inheriting
    potentially incorrect event context.
    """

    if not isinstance(question, str):
        raise ValueError("Question must be text")

    original = question.strip()

    if not original:
        raise ValueError("Question cannot be empty")

    # Never override an explicitly named event.
    if EVENT_ID_PATTERN.search(original):
        return ResolvedConversationQuestion(
            original_question=original,
            retrieval_question=original,
        )

    # Ordinary standalone questions do not require
    # conversation-context resolution.
    if not CONTEXT_REFERENCE_PATTERN.search(original):
        return ResolvedConversationQuestion(
            original_question=original,
            retrieval_question=original,
        )

    # Inspect the most recent retrieval response.
    # Do not reach further back if that response
    # is ambiguous or contains no evidence.
    latest_retrieval = next(
        (
            message
            for message in reversed(messages)
            if message.role == "assistant" and message.kind == "retrieval"
        ),
        None,
    )

    if latest_retrieval is None:
        raise ValueError(
            "Cannot resolve event reference without " "previous retrieval context"
        )

    plan = latest_retrieval.query_plan or {}
    event_id = plan.get("event_id")

    if (
        not isinstance(event_id, str)
        or EVENT_ID_PATTERN.fullmatch(event_id) is None
        or not latest_retrieval.evidence
    ):
        raise ValueError(
            "Cannot resolve event reference from " "ambiguous conversation context"
        )

    event_id = event_id.upper()

    return ResolvedConversationQuestion(
        original_question=original,
        retrieval_question=(f"{original} [Event context: {event_id}]"),
        inherited_event_id=event_id,
    )
