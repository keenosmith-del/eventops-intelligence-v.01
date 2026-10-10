
import csv
import hashlib
import json
from pathlib import Path

from pydantic import BaseModel

from app.models.domain import Event, KnowledgeRecord
from app.models.structured import (
    ParticipantDirectory,
    Policy,
)


DEFAULT_DATA_DIR = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "structured"
)


def _read_csv(
    path: Path,
    expected_columns: list[str],
) -> list[dict]:
    with path.open(
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if reader.fieldnames != expected_columns:
            raise ValueError(
                f"Unexpected CSV columns in {path.name}: "
                f"{reader.fieldnames}"
            )

        rows = list(reader)

    if not rows:
        raise ValueError(f"{path.name} contains no records")

    return rows


def _ensure_unique(
    values: list[str],
    description: str,
) -> None:
    if len(values) != len(set(values)):
        raise ValueError(
            f"Duplicate {description} detected"
        )


def _source_fingerprint(model: BaseModel) -> str:
    payload = model.model_dump(mode="json")

    canonical_json = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()


def _create_record(
    *,
    filename: str,
    record_id: str,
    lookup_field: str,
    record_type: str,
    content: str,
    source_model: BaseModel,
    event_id: str | None = None,
) -> KnowledgeRecord:

    source_path = f"data/structured/{filename}"

    return KnowledgeRecord(
        document_id=filename,
        record_id=record_id,
        content=content,
        event_id=event_id,
        metadata={
            "record_type": record_type,
            "source_path": source_path,
            "source_reference": (
                f"{source_path}#{lookup_field}={record_id}"
            ),
            "source_sha256": _source_fingerprint(
                source_model
            ),
        },
    )


def ingest_structured_documents(
    data_dir: Path | None = None,
) -> list[KnowledgeRecord]:

    source_dir = (
        Path(data_dir)
        if data_dir is not None
        else DEFAULT_DATA_DIR
    )

    event_rows = _read_csv(
        source_dir / "events.csv",
        [
            "event_id",
            "title",
            "starts_at",
            "ends_at",
            "venue",
            "capacity",
        ],
    )

    policy_rows = _read_csv(
        source_dir / "policies.csv",
        [
            "policy_id",
            "event_id",
            "category",
            "rule_text",
        ],
    )

    events = [
        Event.model_validate(row)
        for row in event_rows
    ]

    policies = [
        Policy.model_validate(row)
        for row in policy_rows
    ]

    directory_data = json.loads(
        (source_dir / "directory.json").read_text(
            encoding="utf-8"
        )
    )

    directory = ParticipantDirectory.model_validate(
        directory_data
    )

    event_ids = {event.event_id for event in events}

    _ensure_unique(
        [event.event_id for event in events],
        "event IDs",
    )

    _ensure_unique(
        [policy.policy_id for policy in policies],
        "policy IDs",
    )

    _ensure_unique(
        [
            person.participant_id
            for person in directory.participants
        ],
        "participant IDs",
    )

    _ensure_unique(
        [
            person.email.casefold()
            for person in directory.participants
        ],
        "directory email addresses",
    )

    for policy in policies:
        if (
            policy.event_id != "ALL"
            and policy.event_id not in event_ids
        ):
            raise ValueError(
                f"Policy {policy.policy_id} references "
                f"unknown event {policy.event_id}"
            )

    for person in directory.participants:
        _ensure_unique(
            person.registered_events,
            f"registered events for {person.participant_id}",
        )

        unknown_events = (
            set(person.registered_events) - event_ids
        )

        if unknown_events:
            raise ValueError(
                f"Participant {person.participant_id} "
                f"references unknown event: "
                f"{sorted(unknown_events)}"
            )

    records: list[KnowledgeRecord] = []

    # Each event becomes one self-contained knowledge record.
    for event in events:
        content = (
            f"Event {event.event_id}: {event.title}. "
            f"Starts at: {event.starts_at.isoformat()}. "
            f"Ends at: {event.ends_at.isoformat()}. "
            f"Venue: {event.venue}. "
            f"Capacity: {event.capacity} attendees."
        )

        records.append(
            _create_record(
                filename="events.csv",
                record_id=event.event_id,
                lookup_field="event_id",
                record_type="event",
                content=content,
                source_model=event,
                event_id=event.event_id,
            )
        )

    # Global and event-specific policies retain their scope.
    for policy in policies:
        scope = (
            "all events"
            if policy.event_id == "ALL"
            else f"event {policy.event_id}"
        )

        content = (
            f"Policy {policy.policy_id}. "
            f"Applies to: {scope}. "
            f"Category: {policy.category}. "
            f"Rule: {policy.rule_text}"
        )

        records.append(
            _create_record(
                filename="policies.csv",
                record_id=policy.policy_id,
                lookup_field="policy_id",
                record_type="policy",
                content=content,
                source_model=policy,
                event_id=(
                    None
                    if policy.event_id == "ALL"
                    else policy.event_id
                ),
            )
        )

    # Each participant retains identity and event associations.
    for person in directory.participants:
        registered_events = ", ".join(
            person.registered_events
        )

        content = (
            f"Participant {person.participant_id}: "
            f"{person.full_name}. "
            f"Email: {person.email}. "
            f"Organization: {person.organization}. "
            f"Directory status: {person.status.value}. "
            f"Registered events: {registered_events}."
        )

        record = _create_record(
            filename="directory.json",
            record_id=person.participant_id,
            lookup_field="participant_id",
            record_type="participant",
            content=content,
            source_model=person,
        )

        record.metadata["event_ids"] = (
            ",".join(person.registered_events)
        )

        records.append(record)

    return records
