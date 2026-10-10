import numpy as np
import pytest

from app.core.database import connect_db
from app.models.domain import KnowledgeRecord
from app.rag.ingestion import ingest_structured_documents
from app.services.knowledge_repository import KnowledgeRepository


@pytest.fixture
def repository():
    connection = connect_db()

    try:
        yield KnowledgeRepository(connection)
    finally:
        connection.rollback()
        connection.close()


@pytest.fixture
def sample_record():
    return KnowledgeRecord(
        document_id="integration-test.json",
        record_id="TEST-001",
        content="Test event at a fictional venue.",
        event_id="EVT-101",
        metadata={
            "record_type": "event",
            "source_path": "integration-test.json",
            "source_reference": "integration-test.json#TEST-001",
            "source_sha256": "a" * 64,
        },
    )


def test_insert_and_retrieve_record(repository, sample_record):
    changed = repository.upsert_records([sample_record])

    stored = repository.get_record(
        sample_record.document_id,
        sample_record.record_id,
    )

    assert changed == 1
    assert stored == sample_record


def test_repeated_upsert_does_not_duplicate_records(
    repository,
    sample_record,
):
    assert repository.upsert_records([sample_record]) == 1

    count_before = repository.count_records()

    assert repository.upsert_records([sample_record]) == 0
    assert repository.count_records() == count_before


def test_source_change_invalidates_embedding(
    repository,
    sample_record,
):
    repository.upsert_records([sample_record])

    repository.save_embedding(
        sample_record.document_id,
        sample_record.record_id,
        np.ones(384, dtype=np.float32),
    )

    updated = sample_record.model_copy(deep=True)
    updated.content = "Updated fictional event information."
    updated.metadata["source_sha256"] = "b" * 64

    assert repository.upsert_records([updated]) == 1

    with repository.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT embedding IS NULL
            FROM knowledge_records
            WHERE document_id = %s AND record_id = %s
            """,
            (
                sample_record.document_id,
                sample_record.record_id,
            ),
        )

        assert cursor.fetchone()[0] is True


def test_embedding_is_stored_with_384_dimensions(
    repository,
    sample_record,
):
    repository.upsert_records([sample_record])

    repository.save_embedding(
        sample_record.document_id,
        sample_record.record_id,
        np.ones(384, dtype=np.float32),
    )

    with repository.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT vector_dims(embedding)
            FROM knowledge_records
            WHERE document_id = %s AND record_id = %s
            """,
            (
                sample_record.document_id,
                sample_record.record_id,
            ),
        )

        assert cursor.fetchone()[0] == 384


def test_invalid_embedding_dimensions_are_rejected(
    repository,
    sample_record,
):
    repository.upsert_records([sample_record])

    with pytest.raises(ValueError, match="384"):
        repository.save_embedding(
            sample_record.document_id,
            sample_record.record_id,
            [0.1, 0.2, 0.3],
        )


def test_zero_embedding_is_rejected(
    repository,
    sample_record,
):
    repository.upsert_records([sample_record])

    with pytest.raises(ValueError, match="zero vector"):
        repository.save_embedding(
            sample_record.document_id,
            sample_record.record_id,
            np.zeros(384),
        )


def test_unembedded_records_are_detected(
    repository,
    sample_record,
):
    repository.upsert_records([sample_record])

    pending = repository.list_unembedded_records()

    assert any(
        record.record_id == sample_record.record_id
        and record.document_id == sample_record.document_id
        for record in pending
    )

    repository.save_embedding(
        sample_record.document_id,
        sample_record.record_id,
        np.ones(384),
    )

    pending = repository.list_unembedded_records()

    assert not any(
        record.record_id == sample_record.record_id
        and record.document_id == sample_record.document_id
        for record in pending
    )


def test_missing_record_returns_none(repository):
    result = repository.get_record(
        "nonexistent-document.json",
        "NONEXISTENT",
    )

    assert result is None


def test_authoritative_dataset_can_be_persisted(repository):
    records = ingest_structured_documents()

    repository.upsert_records(records)

    stored = repository.get_record(
        "events.csv",
        "EVT-101",
    )

    assert stored is not None
    assert stored.record_id == "EVT-101"
    assert "AI Engineering Summit" in stored.content
