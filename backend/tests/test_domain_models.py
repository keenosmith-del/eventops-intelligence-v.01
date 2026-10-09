
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models.domain import (
    AgentRun,
    AgentRunStatus,
    Event,
    KnowledgeRecord,
    Registration,
    SourceEvidence,
    SourceType,
    VerificationResult,
    VerificationStatus,
)


EVENT_DATA = {
    "event_id": "EVT-101",
    "title": "AI Engineering Summit",
    "starts_at": datetime(2026, 10, 21, 9, 0, tzinfo=timezone.utc),
    "ends_at": datetime(2026, 10, 21, 17, 0, tzinfo=timezone.utc),
    "venue": "Cape Town Convention Centre",
    "capacity": 150,
}


def test_valid_event():
    event = Event(**EVENT_DATA)

    assert event.event_id == "EVT-101"
    assert event.capacity == 150


def test_event_rejects_invalid_schedule():
    with pytest.raises(ValidationError):
        Event(**{
            **EVENT_DATA,
            "ends_at": EVENT_DATA["starts_at"],
        })


def test_event_rejects_missing_timezone():
    with pytest.raises(ValidationError):
        Event(**{
            **EVENT_DATA,
            "starts_at": datetime(2026, 10, 21, 9, 0),
        })


def test_event_rejects_invalid_capacity():
    with pytest.raises(ValidationError):
        Event(**{**EVENT_DATA, "capacity": 0})


def test_registration_allows_missing_information():
    registration = Registration(
        registration_id="REG-001",
        event_id="EVT-101",
        full_name="Ada Mensah",
    )

    assert registration.email is None
    assert registration.organization is None


def test_knowledge_record_preserves_provenance():
    record = KnowledgeRecord(
        document_id="event-policies",
        record_id="POL-001",
        event_id="EVT-101",
        content="Attendees must check in before 09:00.",
        metadata={"category": "check_in"},
    )

    assert record.record_id == "POL-001"
    assert record.metadata["category"] == "check_in"


def test_source_evidence_has_valid_type():
    evidence = SourceEvidence(
        evidence_id="EVD-001",
        source_type="email",
        source_reference="gmail:message-001",
        source_record_id="REG-001",
    )

    assert evidence.source_type == SourceType.EMAIL
    assert evidence.observed_at.utcoffset() is not None


def test_agent_run_starts_pending():
    run = AgentRun(
        run_id="RUN-001",
        objective="Verify attendees for EVT-101",
    )

    assert run.status == AgentRunStatus.PENDING
    assert run.finished_at is None


def test_verified_result_requires_evidence():
    with pytest.raises(ValidationError):
        VerificationResult(
            registration_id="REG-001",
            event_id="EVT-101",
            status=VerificationStatus.VERIFIED,
        )


def test_verified_result_rejects_unresolved_issues():
    with pytest.raises(ValidationError):
        VerificationResult(
            registration_id="REG-001",
            event_id="EVT-101",
            status=VerificationStatus.VERIFIED,
            evidence_ids=["EVD-001"],
            issues=["Email mismatch"],
        )


def test_review_result_accepts_discrepancies():
    result = VerificationResult(
        registration_id="REG-001",
        event_id="EVT-101",
        status=VerificationStatus.REVIEW_REQUIRED,
        evidence_ids=["EVD-001"],
        issues=["Email mismatch"],
    )

    assert result.status == VerificationStatus.REVIEW_REQUIRED
    assert len(result.issues) == 1
