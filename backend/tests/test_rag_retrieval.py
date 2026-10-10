
import numpy as np
import pytest

from app.rag.ingestion import ingest_structured_documents
from app.rag.retrieval import SemanticRetriever


## Fake embedding model for testing purposes. Simulates the behavior of a real embedding model
class FakeEmbeddingModel:
    def __init__(self):
        self.document_calls = 0
        self.query_calls = 0

    def embed_documents(self, texts):
        self.document_calls += 1

        vectors = []

        for text in texts:
            if text.startswith("Event EVT-101:"):
                vectors.append([1.0, 0.0, 0.0])
            elif text.startswith("Policy POL-003."):
                vectors.append([0.0, 1.0, 0.0])
            else:
                vectors.append([0.0, 0.0, 1.0])

        return np.array(vectors, dtype=np.float32)

    def embed_query(self, query):
        self.query_calls += 1

        if "summit" in query.lower():
            return np.array([1.0, 0.0, 0.0])

        if "check-in" in query.lower():
            return np.array([0.0, 1.0, 0.0])

        return np.array([0.0, 0.0, 1.0])


@pytest.fixture
def search_engine():
    records = ingest_structured_documents()
    model = FakeEmbeddingModel()

    return SemanticRetriever(records, model), model


def test_all_knowledge_records_are_indexed(search_engine):
    retriever, model = search_engine

    assert retriever.record_count == 19
    assert model.document_calls == 1


def test_semantic_search_ranks_event_first(search_engine):
    retriever, _ = search_engine

    results = retriever.search(
        "Tell me about the AI Engineering Summit",
        top_k=3,
    )

    assert results[0].record.record_id == "EVT-101"
    assert results[0].score == pytest.approx(1.0)


def test_semantic_search_ranks_policy_first(search_engine):
    retriever, _ = search_engine

    results = retriever.search(
        "What is the check-in policy?",
        top_k=3,
    )

    assert results[0].record.record_id == "POL-003"


def test_record_type_filter(search_engine):
    retriever, _ = search_engine

    results = retriever.search(
        "Tell me about the summit",
        record_type="policy",
    )

    assert results
    assert all(
        hit.record.metadata["record_type"] == "policy"
        for hit in results
    )


def test_event_filter_includes_registered_participants(search_engine):
    retriever, _ = search_engine

    results = retriever.search(
        "Which participants are registered?",
        event_id="EVT-103",
        record_type="participant",
        top_k=10,
    )

    ids = {hit.record.record_id for hit in results}

    assert ids == {"P-005", "P-006", "P-007"}


def test_event_filter_includes_global_policies(search_engine):
    retriever, _ = search_engine

    results = retriever.search(
        "What are the check-in requirements?",
        event_id="EVT-101",
        record_type="policy",
        top_k=20,
    )

    ids = {hit.record.record_id for hit in results}

    assert "POL-001" in ids
    assert "POL-003" in ids
    assert "POL-009" in ids
    assert "POL-005" not in ids


def test_search_preserves_source_evidence(search_engine):
    retriever, _ = search_engine

    result = retriever.search(
        "AI Engineering Summit",
        top_k=1,
    )[0]

    assert result.record.document_id == "events.csv"
    assert result.record.record_id == "EVT-101"
    assert (
        "event_id=EVT-101"
        in result.record.metadata["source_reference"]
    )
    assert len(
        result.record.metadata["source_sha256"]
    ) == 64


def test_unknown_event_returns_no_results(search_engine):
    retriever, _ = search_engine

    results = retriever.search(
        "Find the event",
        event_id="EVT-999",
    )

    assert results == []


def test_blank_search_is_rejected(search_engine):
    retriever, _ = search_engine

    with pytest.raises(ValueError, match="empty"):
        retriever.search("   ")


@pytest.mark.parametrize("top_k", [0, -1, 1.5, True])
def test_invalid_result_limit_is_rejected(
    search_engine,
    top_k,
):
    retriever, _ = search_engine

    with pytest.raises(ValueError, match="top_k"):
        retriever.search("Event details", top_k=top_k)


def test_empty_knowledge_base_is_rejected():
    with pytest.raises(ValueError, match="without knowledge"):
        SemanticRetriever([], FakeEmbeddingModel())


def test_zero_document_vectors_are_rejected():
    class InvalidModel(FakeEmbeddingModel):
        def embed_documents(self, texts):
            return np.zeros((len(texts), 3))

    with pytest.raises(ValueError, match="zero"):
        SemanticRetriever(
            ingest_structured_documents(),
            InvalidModel(),
        )


def test_invalid_query_dimensions_are_rejected():
    class InvalidModel(FakeEmbeddingModel):
        def embed_query(self, query):
            return np.array([1.0, 0.0])

    retriever = SemanticRetriever(
        ingest_structured_documents(),
        InvalidModel(),
    )

    with pytest.raises(ValueError, match="query embedding"):
        retriever.search("Find event details")


def test_document_embeddings_are_reused(search_engine):
    retriever, model = search_engine

    retriever.search("Summit")
    retriever.search("Check-in requirements")

    assert model.document_calls == 1
    assert model.query_calls == 2


def test_search_results_do_not_expose_internal_records(
    search_engine,
):
    retriever, _ = search_engine

    first = retriever.search("Summit", top_k=1)
    first[0].record.content = "Modified externally"

    second = retriever.search("Summit", top_k=1)

    assert second[0].record.content != "Modified externally"
