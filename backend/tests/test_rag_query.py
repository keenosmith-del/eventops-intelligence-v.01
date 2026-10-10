import numpy as np
import pytest

from app.rag.ingestion import ingest_structured_documents
from app.rag.query import interpret_query, retrieve_question
from app.rag.retrieval import SemanticRetriever


class FlatEmbeddingModel:
    """Controlled embeddings for testing filter behaviour."""

    def embed_documents(self, texts):
        return np.tile(
            np.array([[1.0, 0.0, 0.0]], dtype=np.float32),
            (len(texts), 1),
        )

    def embed_query(self, query):
        return np.array(
            [1.0, 0.0, 0.0],
            dtype=np.float32,
        )


@pytest.fixture
def retriever():
    return SemanticRetriever(
        ingest_structured_documents(),
        FlatEmbeddingModel(),
    )


def test_extracts_and_normalizes_event_id():
    plan = interpret_query("  Where is evt-101 being held?  ")

    assert plan.event_id == "EVT-101"
    assert plan.record_type == "event"


def test_identifies_check_in_policy():
    plan = interpret_query("What time does check-in close for EVT-101?")

    assert plan.record_type == "policy"
    assert plan.policy_category == "check_in"


def test_identifies_inactive_participants():
    plan = interpret_query("Which participants are inactive for EVT-101?")

    assert plan.record_type == "participant"
    assert plan.participant_status == "inactive"


def test_identifies_active_participants():
    plan = interpret_query("Show active attendees for EVT-102")

    assert plan.participant_status == "active"


def test_does_not_overfilter_mixed_status_question():
    plan = interpret_query("List active and inactive participants for EVT-101")

    assert plan.record_type == "participant"
    assert plan.participant_status is None


def test_identifies_event_venue_question():
    plan = interpret_query("What is the venue for EVT-103?")

    assert plan.record_type == "event"


def test_invitation_question_targets_policies():
    plan = interpret_query("Does an invitation guarantee admission to EVT-101?")

    assert plan.record_type == "policy"
    assert plan.policy_category is None


def test_broad_question_does_not_force_record_type():
    plan = interpret_query("Explain the overall operations")

    assert plan.record_type is None


def test_empty_question_is_rejected():
    with pytest.raises(ValueError, match="empty"):
        interpret_query("   ")


def test_multiple_event_identifiers_are_rejected():
    with pytest.raises(
        ValueError,
        match="multiple event IDs",
    ):
        interpret_query("Compare EVT-101 and EVT-102")


def test_inactive_retrieval_returns_only_matching_person(
    retriever,
):
    plan, hits = retrieve_question(
        "Which participants are inactive for EVT-101?",
        retriever,
    )

    assert plan.participant_status == "inactive"
    assert [hit.record.record_id for hit in hits] == ["P-003"]


def test_check_in_retrieval_returns_matching_policy(
    retriever,
):
    plan, hits = retrieve_question(
        "What time does check-in close for EVT-101?",
        retriever,
    )

    assert plan.policy_category == "check_in"
    assert [hit.record.record_id for hit in hits] == ["POL-003"]


def test_global_policies_remain_available(retriever):
    _, hits = retrieve_question(
        "What are the identity requirements for EVT-101?",
        retriever,
        top_k=20,
    )

    ids = {hit.record.record_id for hit in hits}

    assert "POL-001" in ids


def test_unknown_event_returns_no_evidence(retriever):
    _, hits = retrieve_question(
        "Where is EVT-999 being held?",
        retriever,
    )

    assert hits == []


def test_retrieved_results_preserve_provenance(retriever):
    _, hits = retrieve_question(
        "Which participants are inactive for EVT-101?",
        retriever,
    )

    assert len(hits) == 1

    source = hits[0].record.metadata["source_reference"]

    assert source == ("data/structured/directory.json" "#participant_id=P-003")


def test_invalid_participant_filter_is_rejected(retriever):
    with pytest.raises(
        ValueError,
        match="participant status",
    ):
        retriever.search(
            "Find attendees",
            participant_status="suspended",
        )


def test_invalid_policy_category_is_rejected(retriever):
    with pytest.raises(
        ValueError,
        match="policy category",
    ):
        retriever.search(
            "Find policies",
            policy_category="unknown",
        )


## Additional tests for query interpretation
def test_status_verification_does_not_filter_evidence():
    plan = interpret_query("Is Lindi Mokoena active for EVT-101?")

    assert plan.record_type == "participant"
    assert plan.event_id == "EVT-101"
    assert plan.participant_status is None


def test_status_listing_still_filters_participants():
    plan = interpret_query("Which participants are inactive for EVT-101?")

    assert plan.record_type == "participant"
    assert plan.participant_status == "inactive"
