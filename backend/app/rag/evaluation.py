import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from app.rag.query import retrieve_question
from app.rag.retrieval import SearchProvider

DEFAULT_EVALUATION_FILE = (
    Path(__file__).resolve().parents[3] / "data" / "evaluation" / "rag_questions.json"
)


class EvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    expected_record_ids: list[str] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=20)


@dataclass(frozen=True)
class EvaluationOutcome:
    case_id: str
    expected_ids: tuple[str, ...]
    retrieved_ids: tuple[str, ...]
    passed: bool
    recall_at_k: float | None
    reciprocal_rank: float | None


def load_evaluation_cases(
    path: Path = DEFAULT_EVALUATION_FILE,
) -> list[EvaluationCase]:
    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, list) or not data:
        raise ValueError("Evaluation dataset must be a non-empty list")

    cases = [EvaluationCase.model_validate(item) for item in data]

    identifiers = [case.case_id for case in cases]

    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Duplicate evaluation case IDs")

    for case in cases:
        if len(case.expected_record_ids) != len(set(case.expected_record_ids)):
            raise ValueError(f"Duplicate expected records in {case.case_id}")

    return cases


def evaluate_case(
    case: EvaluationCase,
    retriever: SearchProvider,
) -> EvaluationOutcome:

    _, hits = retrieve_question(
        case.question,
        retriever,
        top_k=case.top_k,
    )

    retrieved = tuple(hit.record.record_id for hit in hits)

    expected = tuple(case.expected_record_ids)

    if not expected:
        return EvaluationOutcome(
            case_id=case.case_id,
            expected_ids=expected,
            retrieved_ids=retrieved,
            passed=len(retrieved) == 0,
            recall_at_k=None,
            reciprocal_rank=None,
        )

    expected_set = set(expected)

    found = expected_set.intersection(retrieved)

    recall = len(found) / len(expected_set)

    reciprocal_rank = next(
        (
            1.0 / rank
            for rank, record_id in enumerate(retrieved, start=1)
            if record_id in expected_set
        ),
        0.0,
    )

    return EvaluationOutcome(
        case_id=case.case_id,
        expected_ids=expected,
        retrieved_ids=retrieved,
        passed=recall == 1.0,
        recall_at_k=recall,
        reciprocal_rank=reciprocal_rank,
    )


def main() -> None:
    from app.rag.embeddings import LocalEmbeddingModel
    from app.rag.ingestion import ingest_structured_documents
    from app.rag.retrieval import SemanticRetriever

    print("Loading structured knowledge...")
    records = ingest_structured_documents()

    print("Initializing local embedding model...")
    retriever = SemanticRetriever(
        records,
        LocalEmbeddingModel(),
    )

    cases = load_evaluation_cases()

    outcomes = [evaluate_case(case, retriever) for case in cases]

    print("\nRAG RETRIEVAL EVALUATION — IN-MEMORY")
    print("=" * 60)

    for outcome in outcomes:
        status = "PASS" if outcome.passed else "FAIL"

        print(f"\n{outcome.case_id}: {status}")
        print(f"Expected: {list(outcome.expected_ids)}")
        print(f"Retrieved: {list(outcome.retrieved_ids)}")

    positives = [outcome for outcome in outcomes if outcome.recall_at_k is not None]

    negatives = [outcome for outcome in outcomes if outcome.recall_at_k is None]

    pass_rate = sum(outcome.passed for outcome in outcomes) / len(outcomes)

    mean_recall = (
        sum(outcome.recall_at_k for outcome in positives) / len(positives)
        if positives
        else 0.0
    )

    mrr = (
        sum(outcome.reciprocal_rank for outcome in positives) / len(positives)
        if positives
        else 0.0
    )

    negative_accuracy = (
        sum(outcome.passed for outcome in negatives) / len(negatives)
        if negatives
        else 0.0
    )

    print("\n" + "=" * 60)
    print(f"Cases: {len(outcomes)}")
    print(f"Passing cases: " f"{sum(outcome.passed for outcome in outcomes)}")
    print(f"Pass rate: {pass_rate:.2%}")
    print(f"Mean Recall@K: {mean_recall:.2%}")
    print(f"Mean Reciprocal Rank: {mrr:.4f}")
    print(f"Negative-case accuracy: {negative_accuracy:.2%}")


if __name__ == "__main__":
    main()
