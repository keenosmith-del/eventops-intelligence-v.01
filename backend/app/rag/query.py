import re
from dataclasses import dataclass

from app.rag.retrieval import SearchHit, SearchProvider

# This module provides functions to interpret natural-language questions and retrieve relevant knowledge records
# from a structured knowledge base. It uses regular expressions to identify specific terms in the query that
# indicate the type of information being requested, such as event IDs, participant status, or policy categories.
# The retrieved records are ranked based on their relevance to the query using a semantic retriever.
EVENT_PATTERN = re.compile(
    r"\bEVT-\d+\b",
    flags=re.IGNORECASE,
)

PARTICIPANT_PATTERN = re.compile(
    r"\b(participants?|attendees?|registrants?|" r"directory|active|inactive)\b"
)

POLICY_PATTERN = re.compile(
    r"\b(polic(?:y|ies)|rules?|requirements?|"
    r"check[\s-]?in|cancellations?|transfers?|"
    r"recording|eligibility|invitation|admission)\b"
)

EXPLICIT_POLICY_PATTERN = re.compile(r"\b(polic(?:y|ies)|rules?|requirements?)\b")

EVENT_PATTERN_TERMS = re.compile(
    r"\b(venue|where|when|held|starts?|ends?|"
    r"schedule|capacity|summit|forum|briefing)\b"
)


@dataclass(frozen=True)
class QueryPlan:
    query: str
    event_id: str | None = None
    record_type: str | None = None
    participant_status: str | None = None
    policy_category: str | None = None


def interpret_query(question: str) -> QueryPlan:
    """Convert a natural-language question into search filters."""

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question cannot be empty")

    normalized = " ".join(question.split())
    text = normalized.lower()

    event_ids = list(
        dict.fromkeys(match.upper() for match in EVENT_PATTERN.findall(normalized))
    )

    if len(event_ids) > 1:
        raise ValueError(
            "Queries involving multiple event IDs " "are not yet supported"
        )

    event_id = event_ids[0] if event_ids else None

    has_participant_terms = bool(PARTICIPANT_PATTERN.search(text))
    has_policy_terms = bool(POLICY_PATTERN.search(text))
    explicitly_asks_policy = bool(EXPLICIT_POLICY_PATTERN.search(text))

    record_type = None

    if explicitly_asks_policy:
        record_type = "policy"
    elif has_participant_terms:
        record_type = "participant"
    elif has_policy_terms:
        record_type = "policy"
    elif EVENT_PATTERN_TERMS.search(text):
        record_type = "event"

    participant_status = None

    if record_type == "participant":
        mentions_inactive = bool(re.search(r"\binactive\b", text))
        mentions_active = bool(re.search(r"\bactive\b", text))

        # Questions asking whether a status is true must
        # retrieve the underlying record before checking it.
        # Do not remove contradictory evidence.
        asks_about_status = bool(
            re.match(
                r"^(?:is|was)\s+(?!there\b).*\b" r"(?:active|inactive)\b",
                text,
            )
        )

        if not asks_about_status:
            if mentions_inactive and not mentions_active:
                participant_status = "inactive"
            elif mentions_active and not mentions_inactive:
                participant_status = "active"

    policy_category = None

    if record_type == "policy":
        if re.search(r"\bcheck[\s-]?in\b", text):
            policy_category = "check_in"
        elif re.search(r"\bcancellations?\b", text):
            policy_category = "cancellation"
        elif re.search(r"\btransfers?\b", text):
            policy_category = "transfers"
        elif re.search(r"\brecording\b", text):
            policy_category = "recording"

    # Return a QueryPlan object with the interpreted query and filters
    return QueryPlan(
        query=normalized,
        event_id=event_id,
        record_type=record_type,
        participant_status=participant_status,
        policy_category=policy_category,
    )


def retrieve_question(
    question: str,
    retriever: SearchProvider,
    top_k: int = 5,
) -> tuple[QueryPlan, list[SearchHit]]:
    """Interpret a question and retrieve eligible evidence."""

    plan = interpret_query(question)

    results = retriever.search(
        query=plan.query,
        top_k=top_k,
        record_type=plan.record_type,
        event_id=plan.event_id,
        participant_status=plan.participant_status,
        policy_category=plan.policy_category,
    )

    return plan, results
