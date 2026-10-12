import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from app.rag.generation import GroundedAnswer

DEFAULT_GENERATION_EVALUATION_FILE = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "evaluation"
    / "generation_cases.json"
)


# Evaluation evidence model
class EvaluationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: str = Field(min_length=1)
    source_reference: str = Field(min_length=1)
    content: str = Field(min_length=1)


# Generation evaluation case model
class GenerationEvaluationCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    scenario: str = Field(min_length=1)
    question: str = Field(min_length=1)

    evidence: list[EvaluationEvidence]

    expected_status: Literal[
        "generated",
        "insufficient_evidence",
        "unavailable",
    ]

    required_facts: list[str] = Field(default_factory=list)

    expected_citation_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_expectations(self):
        evidence_ids = [item.record_id for item in self.evidence]

        # Validate uniqueness and consistency of identifiers and facts
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("Duplicate evidence identifiers")

        citations = self.expected_citation_ids

        # Validate uniqueness and consistency of expected citations
        if len(citations) != len(set(citations)):
            raise ValueError("Duplicate expected citations")

        # Validate that expected citations exist in the evidence
        if any(
            not isinstance(fact, str) or not fact.strip()
            for fact in self.required_facts
        ):
            raise ValueError("Required facts must contain text")

        # Validate that expected citations exist in the evidence
        if self.expected_status == "generated":
            if not self.required_facts or not citations:
                raise ValueError(
                    "Generated-answer cases require " "facts and citations"
                )

            if not set(citations).issubset(evidence_ids):
                raise ValueError("Expected citations must exist " "in the evidence")

        # Validate that non-generated cases do not expect answer facts or citations
        elif self.required_facts or citations:
            raise ValueError(
                "Non-generated cases cannot expect " "answer facts or citations"
            )

        return self


@dataclass(frozen=True)
class GenerationEvaluationOutcome:
    case_id: str
    passed: bool
    failures: tuple[str, ...]


def load_generation_evaluation_cases(
    path: Path = DEFAULT_GENERATION_EVALUATION_FILE,
) -> list[GenerationEvaluationCase]:
    data = json.loads(path.read_text(encoding="utf-8"))

    # Validate that the loaded data is a non-empty list of cases
    if not isinstance(data, list) or not data:
        raise ValueError("Generation evaluation requires " "a non-empty case list")

    cases = [GenerationEvaluationCase.model_validate(item) for item in data]

    identifiers = [case.case_id for case in cases]

    # Validate uniqueness of case identifiers
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Duplicate generation evaluation case IDs")

    return cases


def evaluate_generation_case(
    case: GenerationEvaluationCase,
    result: GroundedAnswer,
) -> GenerationEvaluationOutcome:
    """
    Evaluate an answer against reference expectations.

    This is a deterministic reference-based evaluator,
    not a general semantic entailment classifier.
    """

    failures: list[str] = []

    if result.status != case.expected_status:
        failures.append(
            f"Expected status {case.expected_status}, " f"received {result.status}"
        )

    sources = {item.record_id: item for item in case.evidence}

    actual_ids = [citation.record_id for citation in result.citations]

    expected_ids = set(case.expected_citation_ids)

    # Validate uniqueness and consistency of returned citations
    if len(actual_ids) != len(set(actual_ids)):
        failures.append("Duplicate returned citations")

    if set(actual_ids) != expected_ids:
        failures.append(
            "Returned citations do not match " "the expected source records"
        )

    verified_source_content = []

    # Validate that returned citations match the expected source references
    for citation in result.citations:
        source = sources.get(citation.record_id)

        if source is None:
            failures.append(f"Unknown citation: {citation.record_id}")
            continue

        if citation.source_reference != source.source_reference:
            failures.append(f"Incorrect source reference for " f"{citation.record_id}")
            continue

        verified_source_content.append(source.content)

    if case.expected_status == "generated":
        if not result.answer.strip():
            failures.append("Generated answer is empty")

        answer_text = result.answer.casefold()

        cited_text = " ".join(verified_source_content).casefold()

        for fact in case.required_facts:
            normalized = fact.casefold()

            if normalized not in answer_text:
                failures.append(f"Missing expected answer fact: {fact}")

            if normalized not in cited_text:
                failures.append(
                    f"Expected fact not found in " f"cited evidence: {fact}"
                )

    return GenerationEvaluationOutcome(
        case_id=case.case_id,
        passed=not failures,
        failures=tuple(failures),
    )
