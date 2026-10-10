
import csv
import json
from pathlib import Path

from app.models.domain import Event


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "structured"


def read_csv(filename: str) -> list[dict]:
    with (DATA_DIR / filename).open(
        encoding="utf-8", newline=""
    ) as file:
        return list(csv.DictReader(file))


def read_directory() -> dict:
    with (DATA_DIR / "directory.json").open(
        encoding="utf-8"
    ) as file:
        return json.load(file)


def test_three_structured_documents_exist():
    assert (DATA_DIR / "events.csv").is_file()
    assert (DATA_DIR / "policies.csv").is_file()
    assert (DATA_DIR / "directory.json").is_file()


def test_events_follow_domain_contract():
    events = read_csv("events.csv")

    assert len(events) >= 3

    validated = [
        Event.model_validate(event)
        for event in events
    ]

    ids = [event.event_id for event in validated]
    assert len(ids) == len(set(ids))


def test_policies_reference_known_events():
    events = read_csv("events.csv")
    policies = read_csv("policies.csv")

    event_ids = {event["event_id"] for event in events}

    policy_ids = [policy["policy_id"] for policy in policies]

    assert policies
    assert len(policy_ids) == len(set(policy_ids))

    for policy in policies:
        assert policy["event_id"] in event_ids | {"ALL"}
        assert policy["category"].strip()
        assert policy["rule_text"].strip()


def test_directory_references_known_events():
    events = read_csv("events.csv")
    directory = read_directory()

    event_ids = {event["event_id"] for event in events}
    participants = directory["participants"]

    assert directory["schema_version"] == 1
    assert participants

    participant_ids = [
        person["participant_id"]
        for person in participants
    ]

    assert len(participant_ids) == len(set(participant_ids))

    for person in participants:
        assert person["status"] in {"active", "inactive"}
        assert person["registered_events"]
        assert set(person["registered_events"]) <= event_ids


def test_directory_has_unique_reference_emails():
    participants = read_directory()["participants"]

    emails = [
        person["email"].strip().casefold()
        for person in participants
    ]

    assert len(emails) == len(set(emails))


def test_inactive_participant_exists_for_verification():
    participants = read_directory()["participants"]

    inactive = [
        person
        for person in participants
        if person["status"] == "inactive"
    ]

    assert inactive
    assert any(
        "EVT-101" in person["registered_events"]
        for person in inactive
    )
