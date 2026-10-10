import pytest
from fastapi.testclient import TestClient

from app.api.rag import get_rag_retriever
from app.main import app
from app.models.domain import KnowledgeRecord
from app.rag.retrieval import SearchHit


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
            document_id="events.csv",
            record_id="EVT-101",
            event_id="EVT-101",
            content="AI Engineering Summit in Cape Town.",
            metadata={
                "record_type": "event",
                "source_reference": ("data/structured/events.csv" "#event_id=EVT-101"),
                "source_sha256": "a" * 64,
            },
        )

        return [SearchHit(record=record, score=0.91)]


@pytest.fixture
def api_client():
    retriever = FakeRetriever()

    app.dependency_overrides[get_rag_retriever] = lambda: retriever

    try:
        with TestClient(app) as client:
            yield client, retriever
    finally:
        app.dependency_overrides.pop(
            get_rag_retriever,
            None,
        )


def test_retrieval_returns_source_evidence(api_client):
    client, retriever = api_client

    response = client.post(
        "/api/rag/retrieve",
        json={
            "question": "Where is EVT-101 being held?",
            "top_k": 3,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["evidence_count"] == 1
    assert body["query_plan"]["event_id"] == "EVT-101"

    evidence = body["evidence"][0]

    assert evidence["record_id"] == "EVT-101"
    assert evidence["score"] == 0.91
    assert evidence["source_reference"] == (
        "data/structured/events.csv#event_id=EVT-101"
    )

    assert retriever.calls[0]["top_k"] == 3


def test_api_passes_structured_filters(api_client):
    client, retriever = api_client

    response = client.post(
        "/api/rag/retrieve",
        json={"question": ("Which participants are inactive for EVT-101?")},
    )

    assert response.status_code == 200

    call = retriever.calls[0]

    assert call["event_id"] == "EVT-101"
    assert call["record_type"] == "participant"
    assert call["participant_status"] == "inactive"


def test_unknown_event_returns_empty_evidence(api_client):
    client, _ = api_client

    response = client.post(
        "/api/rag/retrieve",
        json={"question": "Where is EVT-999 being held?"},
    )

    assert response.status_code == 200
    assert response.json()["evidence_count"] == 0
    assert response.json()["evidence"] == []


def test_blank_question_is_rejected(api_client):
    client, _ = api_client

    response = client.post(
        "/api/rag/retrieve",
        json={"question": "   "},
    )

    assert response.status_code == 422


def test_invalid_result_limit_is_rejected(api_client):
    client, _ = api_client

    response = client.post(
        "/api/rag/retrieve",
        json={
            "question": "Where is EVT-101?",
            "top_k": 0,
        },
    )

    assert response.status_code == 422


def test_multiple_events_return_validation_error(api_client):
    client, retriever = api_client

    response = client.post(
        "/api/rag/retrieve",
        json={"question": "Compare EVT-101 and EVT-102"},
    )

    assert response.status_code == 422
    assert retriever.calls == []


def test_unknown_request_fields_are_rejected(api_client):
    client, _ = api_client

    response = client.post(
        "/api/rag/retrieve",
        json={
            "question": "Where is EVT-101?",
            "unexpected": "value",
        },
    )

    assert response.status_code == 422
