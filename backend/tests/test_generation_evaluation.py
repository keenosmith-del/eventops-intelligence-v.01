import json

import pytest

from app.rag.generation import Citation, GroundedAnswer
from app.rag.generation_evaluation import (
    evaluate_generation_case,
    load_generation_evaluation_cases,
)


@pytest.fixture
def cases():
    return {case.case_id: case for case in load_generation_evaluation_cases()}


def answer(
    text,
    citations,
    status="generated",
):
    return GroundedAnswer(
        status=status,
        answer=text,
        citations=[
            Citation(
                record_id=record_id,
                source_reference=source_reference,
            )
            for record_id, source_reference in citations
        ],
        model=("gemini-3.5-flash-lite" if status == "generated" else None),
    )


POLICY_SOURCE = "data/structured/policies.csv" "#policy_id=POL-003"

INVITATION_SOURCE = "data/structured/policies.csv" "#policy_id=POL-009"


def test_evaluation_dataset_contains_seven_cases(cases):
    assert len(cases) == 7

    assert set(cases) == {f"GEN-{index:03d}" for index in range(1, 8)}


def test_correct_factual_answer_passes(cases):
    result = answer(
        "Check-in closes at 08:45.",
        [("POL-003", POLICY_SOURCE)],
    )

    outcome = evaluate_generation_case(
        cases["GEN-001"],
        result,
    )

    assert outcome.passed
    assert outcome.failures == ()


def test_wrong_fact_with_valid_citation_fails(cases):
    result = answer(
        "Check-in closes at 09:15.",
        [("POL-003", POLICY_SOURCE)],
    )

    outcome = evaluate_generation_case(
        cases["GEN-001"],
        result,
    )

    assert not outcome.passed
    assert any(
        "Missing expected answer fact" in failure for failure in outcome.failures
    )


def test_invented_citation_fails(cases):
    result = answer(
        "Check-in closes at 08:45.",
        [
            (
                "POL-999",
                "fabricated-source",
            )
        ],
    )

    outcome = evaluate_generation_case(
        cases["GEN-001"],
        result,
    )

    assert not outcome.passed

    assert any("Unknown citation" in failure for failure in outcome.failures)


def test_incorrect_source_reference_fails(cases):
    result = answer(
        "Check-in closes at 08:45.",
        [
            (
                "POL-003",
                "incorrect-source",
            )
        ],
    )

    outcome = evaluate_generation_case(
        cases["GEN-001"],
        result,
    )

    assert not outcome.passed

    assert any("Incorrect source reference" in failure for failure in outcome.failures)


def test_two_source_answer_passes(cases):
    result = answer(
        (
            "Check-in closes at 08:45. "
            "An invitation does not constitute "
            "verified admission."
        ),
        [
            ("POL-003", POLICY_SOURCE),
            ("POL-009", INVITATION_SOURCE),
        ],
    )

    outcome = evaluate_generation_case(
        cases["GEN-003"],
        result,
    )

    assert outcome.passed


def test_missing_second_citation_fails(cases):
    result = answer(
        (
            "Check-in closes at 08:45. "
            "An invitation does not constitute "
            "verified admission."
        ),
        [("POL-003", POLICY_SOURCE)],
    )

    outcome = evaluate_generation_case(
        cases["GEN-003"],
        result,
    )

    assert not outcome.passed

    assert any(
        "Returned citations do not match" in failure for failure in outcome.failures
    )


def test_no_evidence_abstention_passes(cases):
    result = GroundedAnswer(
        status="insufficient_evidence",
        answer="Insufficient source evidence.",
    )

    outcome = evaluate_generation_case(
        cases["GEN-004"],
        result,
    )

    assert outcome.passed


def test_irrelevant_evidence_abstention_passes(cases):
    result = GroundedAnswer(
        status="insufficient_evidence",
        answer="The evidence does not specify parking fees.",
    )

    outcome = evaluate_generation_case(
        cases["GEN-005"],
        result,
    )

    assert outcome.passed


def test_conflicting_evidence_abstention_passes(cases):
    result = GroundedAnswer(
        status="insufficient_evidence",
        answer="The supplied sources disagree.",
    )

    outcome = evaluate_generation_case(
        cases["GEN-006"],
        result,
    )

    assert outcome.passed


def test_unsupported_conflict_resolution_fails(cases):
    result = answer(
        "Check-in closes at 08:45.",
        [("POL-003", POLICY_SOURCE)],
    )

    outcome = evaluate_generation_case(
        cases["GEN-006"],
        result,
    )

    assert not outcome.passed

    assert any("Expected status" in failure for failure in outcome.failures)


def test_context_resolved_answer_passes(cases):
    result = answer(
        "Check-in for EVT-101 closes at 08:45.",
        [("POL-003", POLICY_SOURCE)],
    )

    outcome = evaluate_generation_case(
        cases["GEN-007"],
        result,
    )

    assert outcome.passed


def test_duplicate_case_ids_are_rejected(
    tmp_path,
    cases,
):
    first = cases["GEN-001"].model_dump(mode="json")

    path = tmp_path / "duplicate_cases.json"

    path.write_text(
        json.dumps([first, first]),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Duplicate generation evaluation case IDs",
    ):
        load_generation_evaluation_cases(path)
