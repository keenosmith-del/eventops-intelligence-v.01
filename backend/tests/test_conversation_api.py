from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.conversations import get_conversation_repository
from app.api.rag import get_rag_retriever
from app.core.database import connect_db
from app.main import app
from app.models.domain import KnowledgeRecord
from app.rag.retrieval import SearchHit
from app.services.conversation_repository import ConversationRepository


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
