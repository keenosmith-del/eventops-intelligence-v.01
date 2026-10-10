from uuid import uuid4

import pytest

from app.core.database import connect_db
from app.services.conversation_repository import (
    ConversationRepository,
)


@pytest.fixture
def repository():
    connection = connect_db()

    try:
        yield ConversationRepository(connection)
    finally:
        connection.rollback()
        connection.close()


@pytest.fixture
def sample_evidence():
    return [
        {
            "document_id": "policies.csv",
            "record_id": "POL-003",
            "content": "Check-in closes at 08:45.",
            "score": 0.862,
            "source_reference": ("data/structured/policies.csv" "#policy_id=POL-003"),
        }
    ]


def save_exchange(
    repository,
    conversation_id,
    question="What time does check-in close for EVT-101?",
    evidence=None,
):
    return repository.append_retrieval_exchange(
        conversation_id=conversation_id,
        question=question,
        query_plan={
            "event_id": "EVT-101",
            "record_type": "policy",
        },
        evidence=evidence if evidence is not None else [],
    )


def test_create_and_retrieve_conversation(repository):
    created = repository.create_conversation("EventOps investigation")

    stored = repository.get_conversation(created.id)

    assert stored is not None
    assert stored.id == created.id
    assert stored.title == "EventOps investigation"
    assert stored.created_at.utcoffset() is not None


def test_conversation_title_is_optional(repository):
    conversation = repository.create_conversation()

    assert conversation.title is None
    assert repository.get_conversation(conversation.id) is not None


def test_blank_conversation_title_is_rejected(repository):
    with pytest.raises(ValueError, match="title"):
        repository.create_conversation("   ")


def test_exchange_persists_both_messages(
    repository,
    sample_evidence,
):
    conversation = repository.create_conversation("Policy check")

    messages = save_exchange(
        repository,
        conversation.id,
        evidence=sample_evidence,
    )

    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[0].kind == "question"
    assert messages[1].role == "assistant"
    assert messages[1].kind == "retrieval"

    history = repository.list_messages(conversation.id)

    assert len(history) == 2
    assert history[0].id < history[1].id


def test_evidence_and_query_plan_survive_round_trip(
    repository,
    sample_evidence,
):
    conversation = repository.create_conversation()

    save_exchange(
        repository,
        conversation.id,
        evidence=sample_evidence,
    )

    history = repository.list_messages(conversation.id)
    retrieval = history[1]

    assert retrieval.query_plan["event_id"] == "EVT-101"
    assert retrieval.evidence == sample_evidence
    assert retrieval.evidence[0]["record_id"] == "POL-003"


def test_multiple_exchanges_remain_ordered(repository):
    conversation = repository.create_conversation()

    save_exchange(
        repository,
        conversation.id,
        question="Where is EVT-101?",
    )

    save_exchange(
        repository,
        conversation.id,
        question="What is its check-in policy?",
    )

    messages = repository.list_messages(conversation.id)

    assert len(messages) == 4

    assert [message.role for message in messages] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]

    assert messages[2].content == ("What is its check-in policy?")


def test_missing_conversation_is_rejected(repository):
    unknown_id = uuid4()

    with pytest.raises(LookupError, match="not found"):
        save_exchange(
            repository,
            unknown_id,
        )

    assert repository.list_messages(unknown_id) == []


def test_conversations_remain_isolated(repository):
    first = repository.create_conversation("First")
    second = repository.create_conversation("Second")

    save_exchange(
        repository,
        first.id,
        question="Question for first conversation",
    )

    assert len(repository.list_messages(first.id)) == 2
    assert repository.list_messages(second.id) == []


def test_recent_conversations_can_be_listed(repository):
    first = repository.create_conversation("First")
    second = repository.create_conversation("Second")

    recent = repository.list_recent_conversations(limit=100)

    ids = {conversation.id for conversation in recent}

    assert first.id in ids
    assert second.id in ids


def test_invalid_evidence_is_rejected_without_writes(
    repository,
):
    conversation = repository.create_conversation()

    with pytest.raises(ValueError, match="Evidence"):
        repository.append_retrieval_exchange(
            conversation_id=conversation.id,
            question="Where is EVT-101?",
            query_plan={"event_id": "EVT-101"},
            evidence=[{"record_id": "EVT-101"}],
        )

    assert repository.list_messages(conversation.id) == []


def test_generated_answer_is_persisted_with_citations(
    repository,
    sample_evidence,
):
    conversation = repository.create_conversation()

    save_exchange(
        repository,
        conversation.id,
        evidence=sample_evidence,
    )

    answer = repository.append_generated_answer(
        conversation_id=conversation.id,
        answer="Check-in closes at 08:45.",
        citations=[
            {
                "record_id": "POL-003",
                "source_reference": (
                    "data/structured/policies.csv" "#policy_id=POL-003"
                ),
            }
        ],
        model="gemini-3.5-flash-lite",
    )

    assert answer.role == "assistant"
    assert answer.kind == "answer"
    assert answer.content == "Check-in closes at 08:45."
    assert answer.evidence[0]["record_id"] == "POL-003"

    history = repository.list_messages(conversation.id)

    assert len(history) == 3
    assert [item.kind for item in history] == [
        "question",
        "retrieval",
        "answer",
    ]

    assert history[2].query_plan["generation"]["model"] == ("gemini-3.5-flash-lite")


def test_unsupported_answer_citation_is_rejected(
    repository,
    sample_evidence,
):
    conversation = repository.create_conversation()

    save_exchange(
        repository,
        conversation.id,
        evidence=sample_evidence,
    )

    with pytest.raises(
        ValueError,
        match="unsupported citations",
    ):
        repository.append_generated_answer(
            conversation_id=conversation.id,
            answer="Unsupported answer.",
            citations=[
                {
                    "record_id": "POL-999",
                    "source_reference": "fabricated-source",
                }
            ],
            model="gemini-3.5-flash-lite",
        )

    assert len(repository.list_messages(conversation.id)) == 2


def test_answer_requires_previous_retrieval(repository):
    conversation = repository.create_conversation()

    with pytest.raises(
        ValueError,
        match="preceding retrieval",
    ):
        repository.append_generated_answer(
            conversation_id=conversation.id,
            answer="An answer.",
            citations=[
                {
                    "record_id": "POL-003",
                    "source_reference": "source",
                }
            ],
            model="gemini-3.5-flash-lite",
        )


def test_duplicate_generated_answer_is_rejected(
    repository,
    sample_evidence,
):
    conversation = repository.create_conversation()

    save_exchange(
        repository,
        conversation.id,
        evidence=sample_evidence,
    )

    arguments = {
        "conversation_id": conversation.id,
        "answer": "Check-in closes at 08:45.",
        "citations": [
            {
                "record_id": "POL-003",
                "source_reference": (
                    "data/structured/policies.csv" "#policy_id=POL-003"
                ),
            }
        ],
        "model": "gemini-3.5-flash-lite",
    }

    repository.append_generated_answer(**arguments)

    with pytest.raises(
        ValueError,
        match="preceding retrieval",
    ):
        repository.append_generated_answer(**arguments)

    assert len(repository.list_messages(conversation.id)) == 3


def test_blank_generated_answer_is_rejected(
    repository,
    sample_evidence,
):
    conversation = repository.create_conversation()

    save_exchange(
        repository,
        conversation.id,
        evidence=sample_evidence,
    )

    with pytest.raises(
        ValueError,
        match="Answer",
    ):
        repository.append_generated_answer(
            conversation_id=conversation.id,
            answer="   ",
            citations=[
                {
                    "record_id": "POL-003",
                    "source_reference": (
                        "data/structured/policies.csv" "#policy_id=POL-003"
                    ),
                }
            ],
            model="gemini-3.5-flash-lite",
        )
