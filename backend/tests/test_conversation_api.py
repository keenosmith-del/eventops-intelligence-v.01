from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.conversations import (
    get_answer_generator,
    get_conversation_repository,
)

from app.api.rag import get_rag_retriever
from app.core.database import connect_db
from app.main import app
from app.models.domain import KnowledgeRecord
from app.rag.retrieval import SearchHit
from app.services.conversation_repository import ConversationRepository
from app.rag.generation import Citation, GroundedAnswer


class FakeRetriever:
    def __init__(self):
        self.calls = []

    def search(
        self,
        query,
        top_k=5,
        record_type=None,
        event_id=None,
        participant_status=None,
        policy_category=None,
    ):
        self.calls.append(
            {
                "query": query,
                "top_k": top_k,
                "record_type": record_type,
                "event_id": event_id,
                "participant_status": participant_status,
                "policy_category": policy_category,
            }
        )

        if event_id == "EVT-999":
            return []

        record = KnowledgeRecord(
            document_id="policies.csv",
            record_id="POL-003",
            content="Check-in for EVT-101 closes at 08:45.",
            event_id="EVT-101",
            metadata={
                "record_type": "policy",
                "policy_category": "check_in",
                "source_reference": (
                    "data/structured/policies.csv" "#policy_id=POL-003"
                ),
                "source_sha256": "a" * 64,
            },
        )

        return [
            SearchHit(
                record=record,
                score=0.862,
            )
        ]


@pytest.fixture
def api_client():
    connection = connect_db()
    repository = ConversationRepository(connection)
    retriever = FakeRetriever()

    app.dependency_overrides[get_conversation_repository] = lambda: repository

    app.dependency_overrides[get_rag_retriever] = lambda: retriever

    try:
        with TestClient(app) as client:
            yield client, repository, retriever
    finally:
        app.dependency_overrides.pop(
            get_conversation_repository,
            None,
        )
        app.dependency_overrides.pop(
            get_rag_retriever,
            None,
        )
        app.dependency_overrides.pop(
            get_answer_generator,
            None,
        )

        connection.rollback()
        connection.close()


def create_conversation(client):
    response = client.post(
        "/api/conversations",
        json={"title": "EventOps RAG test"},
    )

    assert response.status_code == 201
    return response.json()["id"]


def test_create_conversation_returns_uuid(api_client):
    client, _, _ = api_client

    conversation_id = create_conversation(client)

    response = client.get(f"/api/conversations/{conversation_id}")

    assert response.status_code == 200
    assert response.json()["conversation"]["id"] == (conversation_id)


def test_recent_conversations_can_be_listed(api_client):
    client, _, _ = api_client

    conversation_id = create_conversation(client)

    response = client.get("/api/conversations")

    assert response.status_code == 200
    assert any(item["id"] == conversation_id for item in response.json())


def test_question_persists_user_and_retrieval_messages(
    api_client,
):
    client, repository, _ = api_client

    conversation_id = create_conversation(client)

    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "question": ("What time does check-in close for EVT-101?"),
            "top_k": 3,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["messages"]) == 2
    assert body["messages"][0]["role"] == "user"
    assert body["messages"][1]["kind"] == "retrieval"

    stored = repository.list_messages(UUID(conversation_id))

    assert len(stored) == 2


def body_id(value):
    from uuid import UUID

    return UUID(value)


def test_history_preserves_evidence_and_query_plan(
    api_client,
):
    client, _, _ = api_client
    conversation_id = create_conversation(client)

    client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"question": ("What time does check-in close for EVT-101?")},
    )

    response = client.get(f"/api/conversations/{conversation_id}")

    assert response.status_code == 200

    messages = response.json()["messages"]
    assert len(messages) == 2

    retrieval = messages[1]

    assert retrieval["query_plan"]["event_id"] == ("EVT-101")

    assert retrieval["evidence"][0]["record_id"] == ("POL-003")

    assert retrieval["evidence"][0]["source_reference"] == (
        "data/structured/policies.csv" "#policy_id=POL-003"
    )


def test_unknown_conversation_returns_404(api_client):
    client, _, retriever = api_client

    response = client.post(
        f"/api/conversations/{uuid4()}/messages",
        json={"question": "Where is EVT-101?"},
    )

    assert response.status_code == 404
    assert retriever.calls == []


def test_invalid_question_does_not_persist_messages(
    api_client,
):
    client, repository, _ = api_client

    conversation_id = create_conversation(client)

    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"question": "Compare EVT-101 and EVT-102"},
    )

    assert response.status_code == 422

    assert repository.list_messages(body_id(conversation_id)) == []


def test_blank_question_is_rejected(api_client):
    client, _, _ = api_client

    conversation_id = create_conversation(client)

    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"question": "   "},
    )

    assert response.status_code == 422


def test_unknown_event_persists_empty_evidence(
    api_client,
):
    client, _, _ = api_client

    conversation_id = create_conversation(client)

    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"question": "Where is EVT-999 being held?"},
    )

    assert response.status_code == 200

    retrieval = response.json()["messages"][1]

    assert retrieval["evidence"] == []
    assert retrieval["content"] == ("Retrieved 0 evidence records.")


def test_invalid_result_limit_is_rejected(api_client):
    client, _, _ = api_client

    conversation_id = create_conversation(client)

    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "question": "Where is EVT-101?",
            "top_k": 0,
        },
    )

    assert response.status_code == 422


def test_unknown_conversation_get_returns_404(api_client):
    client, _, _ = api_client

    response = client.get(f"/api/conversations/{uuid4()}")

    assert response.status_code == 404


def test_invalid_conversation_uuid_returns_422(
    api_client,
):
    client, _, _ = api_client

    response = client.get("/api/conversations/not-a-uuid")

    assert response.status_code == 422


def test_follow_up_uses_persisted_event_context(api_client):
    client, _, retriever = api_client

    conversation_id = create_conversation(client)

    first = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"question": ("What is the check-in policy for EVT-101?")},
    )

    assert first.status_code == 200

    second = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"question": ("What time does its check-in close?")},
    )

    assert second.status_code == 200

    body = second.json()
    user_message, retrieval_message = body["messages"]

    # The actual user wording must be preserved.
    assert user_message["content"] == ("What time does its check-in close?")

    # The retrieval query must inherit EVT-101.
    last_call = retriever.calls[-1]

    assert last_call["event_id"] == "EVT-101"
    assert last_call["record_type"] == "policy"
    assert last_call["policy_category"] == "check_in"

    assert "EVT-101" in last_call["query"]

    # The resolution decision must be auditable.
    plan = retrieval_message["query_plan"]

    assert plan["context_resolution"] == {
        "used_context": True,
        "inherited_event_id": "EVT-101",
    }

    # Both exchanges must be stored in order.
    history_response = client.get(f"/api/conversations/{conversation_id}")

    assert history_response.status_code == 200

    history = history_response.json()["messages"]

    assert len(history) == 4
    assert history[2]["content"] == ("What time does its check-in close?")
    assert history[3]["evidence"][0]["record_id"] == ("POL-003")


def test_follow_up_without_context_returns_422(api_client):
    client, _, retriever = api_client

    conversation_id = create_conversation(client)

    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"question": ("What time does its check-in close?")},
    )

    assert response.status_code == 422

    assert "previous retrieval context" in (response.json()["detail"])

    assert retriever.calls == []

    history = client.get(f"/api/conversations/{conversation_id}").json()["messages"]

    assert history == []


def test_ambiguous_history_does_not_invent_event(
    api_client,
):
    client, _, retriever = api_client

    conversation_id = create_conversation(client)

    first = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"question": ("What are the general identity requirements?")},
    )

    assert first.status_code == 200

    calls_before = len(retriever.calls)

    second = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"question": ("What is its check-in policy?")},
    )

    assert second.status_code == 422

    assert "ambiguous" in second.json()["detail"]

    # The failed question must not invoke retrieval.
    assert len(retriever.calls) == calls_before

    history = client.get(f"/api/conversations/{conversation_id}").json()["messages"]

    # Only the first, successful exchange is stored.
    assert len(history) == 2


def test_explicit_event_overrides_prior_context(
    api_client,
):
    client, _, retriever = api_client

    conversation_id = create_conversation(client)

    first = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"question": ("What is the check-in policy for EVT-101?")},
    )

    assert first.status_code == 200

    second = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"question": ("What is the check-in policy for EVT-102?")},
    )

    assert second.status_code == 200

    assert retriever.calls[-1]["event_id"] == ("EVT-102")

    plan = second.json()["messages"][1]["query_plan"]

    assert plan["context_resolution"] == {
        "used_context": False,
        "inherited_event_id": None,
    }


def fake_generated_answer(question, evidence):
    assert evidence
    assert evidence[0]["record_id"] == "POL-003"

    return GroundedAnswer(
        status="generated",
        answer="Check-in closes at 08:45.",
        citations=[
            Citation(
                record_id="POL-003",
                source_reference=("data/structured/policies.csv" "#policy_id=POL-003"),
            )
        ],
        model="gemini-3.5-flash-lite",
    )


def test_generation_is_not_requested_by_default(
    api_client,
):
    client, _, _ = api_client

    def unexpected_generation(question, evidence):
        raise AssertionError("Generation must be opt-in")

    app.dependency_overrides[get_answer_generator] = lambda: unexpected_generation

    conversation_id = create_conversation(client)

    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"question": ("What time does check-in close for EVT-101?")},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["generation_status"] == "not_requested"
    assert len(body["messages"]) == 2


def test_generated_answer_is_persisted_through_api(
    api_client,
):
    client, _, _ = api_client

    app.dependency_overrides[get_answer_generator] = lambda: fake_generated_answer

    conversation_id = create_conversation(client)

    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "question": ("What time does check-in close for EVT-101?"),
            "generate_answer": True,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["generation_status"] == "generated"
    assert len(body["messages"]) == 3

    answer = body["messages"][2]

    assert answer["role"] == "assistant"
    assert answer["kind"] == "answer"
    assert answer["content"] == ("Check-in closes at 08:45.")

    assert answer["evidence"][0]["record_id"] == ("POL-003")

    assert answer["query_plan"]["generation"]["model"] == ("gemini-3.5-flash-lite")

    history_response = client.get(f"/api/conversations/{conversation_id}")

    assert history_response.status_code == 200

    stored = history_response.json()["messages"]

    assert [message["kind"] for message in stored] == [
        "question",
        "retrieval",
        "answer",
    ]


def test_unavailable_generation_preserves_retrieval(
    api_client,
):
    client, _, _ = api_client

    def unavailable_generator(question, evidence):
        return GroundedAnswer(
            status="unavailable",
            answer="Generation is unavailable.",
        )

    app.dependency_overrides[get_answer_generator] = lambda: unavailable_generator

    conversation_id = create_conversation(client)

    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "question": "Where is EVT-101?",
            "generate_answer": True,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["generation_status"] == "unavailable"
    assert (
        next(
            m
            for m in client.get(f"/api/conversations/{conversation_id}").json()[
                "messages"
            ]
            if m["kind"] == "retrieval"
        )["query_plan"]["generation_status"]
        == "unavailable"
    )
    assert len(body["messages"]) == 2

    assert body["messages"][1]["evidence"][0]["record_id"] == "POL-003"


def test_insufficient_evidence_does_not_save_answer(
    api_client,
):
    client, _, _ = api_client

    def insufficient_generator(question, evidence):
        assert evidence == []

        return GroundedAnswer(
            status="insufficient_evidence",
            answer="Insufficient source evidence.",
        )

    app.dependency_overrides[get_answer_generator] = lambda: insufficient_generator

    conversation_id = create_conversation(client)

    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "question": "Where is EVT-999 being held?",
            "generate_answer": True,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["generation_status"] == ("insufficient_evidence")

    assert len(body["messages"]) == 2
    assert body["messages"][1]["evidence"] == []


def test_unsupported_generation_citation_is_rejected(
    api_client,
):
    client, _, _ = api_client

    def invalid_generator(question, evidence):
        return GroundedAnswer(
            status="generated",
            answer="An unsupported answer.",
            citations=[
                Citation(
                    record_id="POL-999",
                    source_reference="fabricated-source",
                )
            ],
            model="gemini-3.5-flash-lite",
        )

    app.dependency_overrides[get_answer_generator] = lambda: invalid_generator

    conversation_id = create_conversation(client)

    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "question": "Where is EVT-101?",
            "generate_answer": True,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["generation_status"] == "unavailable"
    assert (
        next(
            m
            for m in client.get(f"/api/conversations/{conversation_id}").json()[
                "messages"
            ]
            if m["kind"] == "retrieval"
        )["query_plan"]["generation_status"]
        == "unavailable"
    )

    # The rejected answer must not be persisted.
    assert len(body["messages"]) == 2

    history = client.get(f"/api/conversations/{conversation_id}").json()["messages"]

    assert len(history) == 2


def test_follow_up_context_survives_generated_answer(
    api_client,
):
    client, _, _ = api_client

    app.dependency_overrides[get_answer_generator] = lambda: fake_generated_answer

    conversation_id = create_conversation(client)

    first = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "question": ("What is the check-in policy for EVT-101?"),
            "generate_answer": True,
        },
    )

    assert first.status_code == 200
    assert first.json()["generation_status"] == "generated"

    second = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "question": ("What time does its check-in close?"),
            "generate_answer": True,
        },
    )

    assert second.status_code == 200
    assert second.json()["generation_status"] == "generated"

    history = client.get(f"/api/conversations/{conversation_id}").json()["messages"]

    assert len(history) == 6

    assert [message["kind"] for message in history] == [
        "question",
        "retrieval",
        "answer",
        "question",
        "retrieval",
        "answer",
    ]

    follow_up = history[4]["query_plan"]

    assert follow_up["event_id"] == "EVT-101"

    assert follow_up["context_resolution"] == {
        "used_context": True,
        "inherited_event_id": "EVT-101",
    }

    assert history[5]["evidence"][0]["record_id"] == "POL-003"


@pytest.mark.parametrize(
    "outcome", ["not_requested", "unavailable", "insufficient_evidence", "generated"]
)
def test_generation_outcome_survives_database_restore(api_client, outcome):
    client, repository, _ = api_client
    conversation_id = create_conversation(client)

    def generator(question, evidence):
        return GroundedAnswer(
            status=outcome,
            answer="Check-in closes at 08:45 SAST." if outcome == "generated" else "",
            citations=(
                [
                    Citation(
                        record_id=evidence[0]["record_id"],
                        source_reference=evidence[0]["source_reference"],
                    )
                ]
                if outcome == "generated"
                else []
            ),
            model="test-provider" if outcome == "generated" else None,
        )

    app.dependency_overrides[get_answer_generator] = lambda: generator
    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={
            "question": "What time does check-in close for EVT-101?",
            "generate_answer": outcome != "not_requested",
        },
    )
    assert response.status_code == 200
    assert response.json()["generation_status"] == outcome
    restored = client.get(f"/api/conversations/{conversation_id}").json()
    retrieval = next(
        message for message in restored["messages"] if message["kind"] == "retrieval"
    )
    assert retrieval["query_plan"]["generation_status"] == outcome
