import shutil
from collections import Counter
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.rag.ingestion import ingest_structured_documents

SOURCE_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "structured"


def copy_dataset(tmp_path: Path) -> Path:
    target = tmp_path / "structured"
    target.mkdir()

    for filename in (
        "events.csv",
        "policies.csv",
        "directory.json",
    ):
        shutil.copy2(
            SOURCE_DATA_DIR / filename,
            target / filename,
        )

    return target


def find_record(records, record_id):
    return next(record for record in records if record.record_id == record_id)


def test_ingestion_generates_all_knowledge_records():
    records = ingest_structured_documents()

    assert len(records) == 19

    counts = Counter(record.metadata["record_type"] for record in records)

    assert counts == {
        "event": 3,
        "policy": 9,
        "participant": 7,
    }


def test_every_record_preserves_source_provenance():
    records = ingest_structured_documents()

    for record in records:
        assert record.document_id
        assert record.record_id
        assert record.content

        assert record.metadata["source_path"]
        assert record.metadata["source_reference"]
        assert len(record.metadata["source_sha256"]) == 64


def test_event_chunk_preserves_structured_information():
    records = ingest_structured_documents()
    event = find_record(records, "EVT-101")

    assert event.event_id == "EVT-101"
    assert "AI Engineering Summit" in event.content
    assert "Cape Town Convention Centre" in event.content
    assert "150 attendees" in event.content
    assert "event_id=EVT-101" in (event.metadata["source_reference"])


def test_global_policy_preserves_applicability():
    records = ingest_structured_documents()
    policy = find_record(records, "POL-001")

    assert policy.event_id is None
    assert "all events" in policy.content
    assert policy.metadata["record_type"] == "policy"


def test_participant_chunk_preserves_reference_status():
    records = ingest_structured_documents()
    participant = find_record(records, "P-003")

    assert "Lindi Mokoena" in participant.content
    assert "Directory status: inactive" in (participant.content)
    assert "EVT-101" in participant.metadata["event_ids"]


def test_repeated_ingestion_is_deterministic():
    first = ingest_structured_documents()
    second = ingest_structured_documents()

    assert first == second


def test_unknown_policy_event_is_rejected(tmp_path):
    data_dir = copy_dataset(tmp_path)
    path = data_dir / "policies.csv"

    content = path.read_text(encoding="utf-8")
    content = content.replace(
        "POL-003,EVT-101",
        "POL-003,EVT-999",
    )
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="unknown event"):
        ingest_structured_documents(data_dir)


def test_unknown_participant_event_is_rejected(tmp_path):
    data_dir = copy_dataset(tmp_path)
    path = data_dir / "directory.json"

    content = path.read_text(encoding="utf-8")
    content = content.replace(
        '"registered_events": ["EVT-101"]',
        '"registered_events": ["EVT-999"]',
        1,
    )
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="unknown event"):
        ingest_structured_documents(data_dir)


def test_duplicate_event_identifiers_are_rejected(tmp_path):
    data_dir = copy_dataset(tmp_path)
    path = data_dir / "events.csv"

    content = path.read_text(encoding="utf-8")
    first_record = content.splitlines()[1]

    path.write_text(
        content.rstrip() + "\n" + first_record + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate event IDs"):
        ingest_structured_documents(data_dir)


def test_invalid_participant_status_is_rejected(tmp_path):
    data_dir = copy_dataset(tmp_path)
    path = data_dir / "directory.json"

    content = path.read_text(encoding="utf-8")
    content = content.replace(
        '"status": "inactive"',
        '"status": "suspended"',
    )
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValidationError):
        ingest_structured_documents(data_dir)


def test_source_fingerprint_changes_with_content(tmp_path):
    data_dir = copy_dataset(tmp_path)

    before = find_record(
        ingest_structured_documents(data_dir),
        "EVT-101",
    )

    path = data_dir / "events.csv"
    content = path.read_text(encoding="utf-8")
    content = content.replace(
        "AI Engineering Summit",
        "AI Systems Summit",
    )
    path.write_text(content, encoding="utf-8")

    after = find_record(
        ingest_structured_documents(data_dir),
        "EVT-101",
    )

    assert before.metadata["source_sha256"] != (after.metadata["source_sha256"])

    assert before.metadata["source_reference"] == (after.metadata["source_reference"])
