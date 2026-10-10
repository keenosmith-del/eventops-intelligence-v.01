import json

import httpx
import pytest

from app.rag import generation


@pytest.fixture(autouse=True)
def disable_live_gemini(monkeypatch):
    monkeypatch.setenv("GEMINI_ENABLED", "false")
    monkeypatch.setenv("GEMINI_API_KEY", "")


@pytest.fixture
def evidence():
    return [
        {
            "record_id": "POL-003",
            "source_reference": ("data/structured/policies.csv" "#policy_id=POL-003"),
            "content": ("Check-in for EVT-101 closes at 08:45."),
        }
    ]


def mock_response(answer, citations):
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps(
                                {
                                    "answer": answer,
                                    "citation_ids": citations,
                                }
                            )
                        }
                    ]
                }
            }
        ]
    }


def test_generation_disabled_by_default(evidence):
    called = []

    def handler(request):
        called.append(request)
        return httpx.Response(500)

    result = generation.generate_grounded_answer(
        "When does check-in close?",
        evidence,
        transport=httpx.MockTransport(handler),
    )

    assert result.status == "unavailable"
    assert called == []


def test_missing_evidence_never_calls_provider(monkeypatch):
    monkeypatch.setenv("GEMINI_ENABLED", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    called = []

    def handler(request):
        called.append(request)
        return httpx.Response(200)

    result = generation.generate_grounded_answer(
        "When does check-in close?",
        [],
        transport=httpx.MockTransport(handler),
    )

    assert result.status == "insufficient_evidence"
    assert called == []


def test_missing_key_prevents_generation(
    monkeypatch,
    evidence,
):
    monkeypatch.setenv("GEMINI_ENABLED", "true")

    result = generation.generate_grounded_answer(
        "When does check-in close?",
        evidence,
    )

    assert result.status == "unavailable"


def test_generated_answer_has_verified_citation_id(
    monkeypatch,
    evidence,
):
    monkeypatch.setenv("GEMINI_ENABLED", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    calls = []

    def handler(request):
        calls.append(request)

        assert generation.GEMINI_MODEL in str(request.url)

        body = json.loads(request.content)

        assert body["generationConfig"]["maxOutputTokens"] == 512

        assert "tools" not in body

        return httpx.Response(
            200,
            json=mock_response(
                "Check-in closes at 08:45.",
                ["POL-003"],
            ),
        )

    result = generation.generate_grounded_answer(
        "When does check-in close?",
        evidence,
        transport=httpx.MockTransport(handler),
    )

    assert result.status == "generated"
    assert result.answer == "Check-in closes at 08:45."
    assert result.model == "gemini-3.5-flash-lite"

    assert len(result.citations) == 1
    assert result.citations[0].record_id == "POL-003"
    assert result.citations[0].source_reference == (
        "data/structured/policies.csv" "#policy_id=POL-003"
    )

    assert len(calls) == 1


def test_invented_citation_is_rejected(
    monkeypatch,
    evidence,
):
    monkeypatch.setenv("GEMINI_ENABLED", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    def handler(request):
        return httpx.Response(
            200,
            json=mock_response(
                "An unsupported claim.",
                ["POL-999"],
            ),
        )

    result = generation.generate_grounded_answer(
        "When does check-in close?",
        evidence,
        transport=httpx.MockTransport(handler),
    )

    assert result.status == "unavailable"
    assert result.citations == []


def test_model_can_abstain(
    monkeypatch,
    evidence,
):
    monkeypatch.setenv("GEMINI_ENABLED", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    def handler(request):
        return httpx.Response(
            200,
            json=mock_response("", []),
        )

    result = generation.generate_grounded_answer(
        "What is the parking fee?",
        evidence,
        transport=httpx.MockTransport(handler),
    )

    assert result.status == "insufficient_evidence"


def test_invalid_model_json_is_rejected(
    monkeypatch,
    evidence,
):
    monkeypatch.setenv("GEMINI_ENABLED", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    def handler(request):
        return httpx.Response(
            200,
            json={"candidates": [{"content": {"parts": [{"text": "not valid JSON"}]}}]},
        )

    result = generation.generate_grounded_answer(
        "When does check-in close?",
        evidence,
        transport=httpx.MockTransport(handler),
    )

    assert result.status == "unavailable"


def test_rate_limit_does_not_trigger_retry(
    monkeypatch,
    evidence,
):
    monkeypatch.setenv("GEMINI_ENABLED", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(429)

    result = generation.generate_grounded_answer(
        "When does check-in close?",
        evidence,
        transport=httpx.MockTransport(handler),
    )

    assert result.status == "unavailable"
    assert len(calls) == 1
