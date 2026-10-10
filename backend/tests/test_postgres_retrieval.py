import numpy as np
import pytest

from app.core.database import connect_db
from app.models.domain import KnowledgeRecord
from app.rag.postgres_retrieval import PostgresSemanticRetriever
from app.rag.query import retrieve_question
from app.services.knowledge_repository import KnowledgeRepository


def make_vector(dimension: int) -> np.ndarray:
    vector = np.zeros(384, dtype=np.float32)
    vector[dimension] = 1.0
    return vector


class FakeEmbeddingModel:
    def __init__(self):
        self.query_calls = 0

    def embed_documents(self, texts):
        return np.array([make_vector(0) for _ in texts])

    def embed_query(self, query):
        self.query_calls += 1

        if "check-in" in query.lower():
            return make_vector(1)

        if "identity" in query.lower():
            return make_vector(2)

        return make_vector(0)


def make_record(
    record_id: str,
    record_type: str,
    content: str,
    event_id: str | None,
    **extra_metadata,
) -> KnowledgeRecord:
    return KnowledgeRecord(
        document_id="pgvector-test.json",
        record_id=record_id,
        content=content,
        event_id=event_id,
        metadata={
            "record_type": record_type,
            "source_path": "pgvector-test.json",
            "source_reference": (f"pgvector-test.json#record_id={record_id}"),
            "source_sha256": "a" * 64,
            **extra_metadata,
        },
    )


@pytest.fixture
def postgres_retriever():
    connection = connect_db()
    model = FakeEmbeddingModel()

    fixtures = [
        (
            make_record(
                "EVT-901",
                "event",
                "Test event EVT-901 at Venue A.",
                "EVT-901",
            ),
            0,
        ),
        (
            make_record(
                "EVT-902",
                "event",
                "Test event EVT-902 at Venue B.",
                "EVT-902",
            ),
            1,
        ),
        (
            make_record(
                "POL-901",
                "policy",
                "Check-in closes at 08:45 for EVT-901.",
                "EVT-901",
                policy_category="check_in",
            ),
            1,
        ),
        (
            make_record(
                "POL-902",
                "policy",
                "All attendees must present identification.",
                None,
                policy_category="identity",
            ),
            2,
        ),
        (
            make_record(
                "P-901",
                "participant",
                "Test Participant One is inactive.",
                None,
                participant_status="inactive",
                event_ids="EVT-901",
            ),
            2,
        ),
        (
            make_record(
                "P-902",
                "participant",
                "Test Participant Two is active.",
                None,
                participant_status="active",
                event_ids="EVT-901",
            ),
            0,
        ),
    ]

    try:
        repository = KnowledgeRepository(connection)

        repository.upsert_records([record for record, _ in fixtures])

        for record, dimension in fixtures:
            repository.save_embedding(
                record.document_id,
                record.record_id,
                make_vector(dimension),
            )

        retriever = PostgresSemanticRetriever(
            connection,
            model,
        )

        yield retriever, model, repository

    finally:
        connection.rollback()
        connection.close()


def test_pgvector_ranks_by_cosine_similarity(
    postgres_retriever,
):
    retriever, _, _ = postgres_retriever

    hits = retriever.search(
        "Find event details",
        record_type="event",
        top_k=10,
    )

    assert hits[0].record.record_id == "EVT-901"
    assert hits[0].score == pytest.approx(1.0)


def test_pgvector_filters_inactive_participants(
    postgres_retriever,
):
    retriever, _, _ = postgres_retriever

    hits = retriever.search(
        "Find inactive attendees",
        event_id="EVT-901",
        record_type="participant",
        participant_status="inactive",
    )

    assert [hit.record.record_id for hit in hits] == ["P-901"]


def test_pgvector_includes_global_policies(
    postgres_retriever,
):
    retriever, _, _ = postgres_retriever

    hits = retriever.search(
        "Identity requirements",
        event_id="EVT-901",
        record_type="policy",
        policy_category="identity",
        top_k=20,
    )

    ids = {hit.record.record_id for hit in hits}

    assert "POL-902" in ids


def test_query_planner_works_with_postgres(
    postgres_retriever,
):
    retriever, _, _ = postgres_retriever

    plan, hits = retrieve_question(
        "What time does check-in close for EVT-901?",
        retriever,
    )

    assert plan.policy_category == "check_in"

    assert [hit.record.record_id for hit in hits] == ["POL-901"]


def test_unknown_event_skips_embedding(
    postgres_retriever,
):
    retriever, model, _ = postgres_retriever

    hits = retriever.search(
        "Where is the unknown event?",
        event_id="EVT-999998",
    )

    assert hits == []
    assert model.query_calls == 0


def test_pgvector_preserves_source_provenance(
    postgres_retriever,
):
    retriever, _, _ = postgres_retriever

    hits = retriever.search(
        "Find event details",
        event_id="EVT-901",
        record_type="event",
    )

    assert len(hits) == 1

    record = hits[0].record

    assert record.document_id == "pgvector-test.json"
    assert record.record_id == "EVT-901"
    assert record.metadata["source_reference"] == (
        "pgvector-test.json#record_id=EVT-901"
    )


def test_invalid_query_vector_is_rejected(
    postgres_retriever,
):
    retriever, _, _ = postgres_retriever

    class InvalidEmbeddingModel:
        def embed_query(self, query):
            return np.array([1.0, 0.0, 0.0])

    retriever.embedding_model = InvalidEmbeddingModel()

    with pytest.raises(ValueError, match="384"):
        retriever.search("Find event details")


def test_invalid_participant_status_is_rejected(
    postgres_retriever,
):
    retriever, _, _ = postgres_retriever

    with pytest.raises(
        ValueError,
        match="participant status",
    ):
        retriever.search(
            "Find attendees",
            participant_status="unknown",
        )


def test_records_without_embeddings_are_excluded(
    postgres_retriever,
):
    retriever, _, repository = postgres_retriever

    repository.upsert_records(
        [
            make_record(
                "EVT-903",
                "event",
                "Not yet embedded event.",
                "EVT-903",
            )
        ]
    )

    hits = retriever.search(
        "Find event details",
        record_type="event",
        top_k=100,
    )

    ids = {hit.record.record_id for hit in hits}

    assert "EVT-903" not in ids
