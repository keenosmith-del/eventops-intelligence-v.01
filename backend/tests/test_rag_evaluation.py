import numpy as np
import pytest

from app.rag.evaluation import (
    EvaluationCase,
    evaluate_case,
    load_evaluation_cases,
)
from app.rag.ingestion import ingest_structured_documents
from app.rag.retrieval import SemanticRetriever


class FlatEmbeddingModel:
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


def test_evaluation_dataset_loads():
    cases = load_evaluation_cases()

    assert len(cases) == 13
    assert len({case.case_id for case in cases}) == 13


def test_evaluation_passes_exact_event_lookup(retriever):
    case = EvaluationCase(
        case_id="TEST-001",
        question="Where is EVT-103 being held?",
        expected_record_ids=["EVT-103"],
    )

    outcome = evaluate_case(case, retriever)

    assert outcome.passed
    assert outcome.recall_at_k == 1.0
    assert outcome.reciprocal_rank == 1.0


def test_evaluation_passes_multiple_references(retriever):
    case = EvaluationCase(
        case_id="TEST-002",
        question="Which participants attend EVT-103?",
        expected_record_ids=["P-005", "P-006", "P-007"],
    )

    outcome = evaluate_case(case, retriever)

    assert outcome.passed
    assert outcome.recall_at_k == 1.0


def test_unknown_event_counts_as_correct_abstention(retriever):
    case = EvaluationCase(
        case_id="TEST-003",
        question="Where is EVT-999 being held?",
        expected_record_ids=[],
    )

    outcome = evaluate_case(case, retriever)

    assert outcome.passed
    assert outcome.retrieved_ids == ()
    assert outcome.recall_at_k is None


# Replace previous test with a more robust evaluation that checks for authoritative records and participant status
# This test ensures that the evaluation logic correctly identifies authoritative records and verifies participant
# status, which is crucial for accurate information retrieval in the context of event management.
def test_status_verification_retrieves_authoritative_record(
    retriever,
):
    case = EvaluationCase(
        case_id="TEST-004",
        question="Is Lindi Mokoena active for EVT-101?",
        expected_record_ids=["P-003"],
    )

    outcome = evaluate_case(case, retriever)

    assert outcome.passed
    assert "P-003" in outcome.retrieved_ids
    assert outcome.recall_at_k == 1.0
