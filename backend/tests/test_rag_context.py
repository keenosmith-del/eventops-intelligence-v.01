from types import SimpleNamespace

import pytest

from app.rag.context import resolve_conversation_question
from app.rag.query import interpret_query


def retrieval_message(
    event_id,
    evidence=None,
):
    return SimpleNamespace(
        role="assistant",
        kind="retrieval",
        query_plan={
            "event_id": event_id,
        },
        evidence=(evidence if evidence is not None else [{"record_id": "EVT-101"}]),
    )


def test_explicit_event_is_preserved():
    result = resolve_conversation_question(
        "Where is EVT-102?",
        [retrieval_message("EVT-101")],
    )

    assert result.retrieval_question == ("Where is EVT-102?")
    assert result.inherited_event_id is None
    assert not result.used_context


def test_follow_up_inherits_event():
    result = resolve_conversation_question(
        "What time does its check-in close?",
        [retrieval_message("EVT-101")],
    )

    assert result.used_context
    assert result.inherited_event_id == "EVT-101"
    assert "EVT-101" in result.retrieval_question


def test_follow_up_is_understood_by_existing_query_planner():
    resolved = resolve_conversation_question(
        "What time does its check-in close?",
        [retrieval_message("EVT-101")],
    )

    plan = interpret_query(resolved.retrieval_question)

    assert plan.event_id == "EVT-101"
    assert plan.record_type == "policy"
    assert plan.policy_category == "check_in"


def test_same_event_phrase_resolves():
    result = resolve_conversation_question(
        "What is the policy for the same event?",
        [retrieval_message("EVT-103")],
    )

    assert result.inherited_event_id == "EVT-103"


def test_most_recent_retrieval_takes_precedence():
    history = [
        retrieval_message("EVT-101"),
        retrieval_message("EVT-102"),
    ]

    result = resolve_conversation_question(
        "What is its check-in policy?",
        history,
    )

    assert result.inherited_event_id == "EVT-102"


def test_missing_conversation_context_fails():
    with pytest.raises(
        ValueError,
        match="previous retrieval context",
    ):
        resolve_conversation_question(
            "What time does its check-in close?",
            [],
        )


def test_ambiguous_context_fails():
    with pytest.raises(
        ValueError,
        match="ambiguous",
    ):
        resolve_conversation_question(
            "What is its policy?",
            [retrieval_message(None)],
        )


def test_empty_evidence_fails():
    with pytest.raises(
        ValueError,
        match="ambiguous",
    ):
        resolve_conversation_question(
            "What is its policy?",
            [
                retrieval_message(
                    "EVT-101",
                    evidence=[],
                )
            ],
        )


def test_standalone_question_is_unchanged():
    result = resolve_conversation_question(
        "What is the participant eligibility policy?",
        [retrieval_message("EVT-101")],
    )

    assert result.retrieval_question == ("What is the participant eligibility policy?")
    assert not result.used_context


def test_empty_question_is_rejected():
    with pytest.raises(
        ValueError,
        match="empty",
    ):
        resolve_conversation_question(
            "   ",
            [],
        )
