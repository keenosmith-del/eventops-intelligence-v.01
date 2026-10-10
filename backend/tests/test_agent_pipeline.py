import json
from copy import deepcopy
from pathlib import Path

from app.rag.ingestion import ingest_structured_documents
from app.verification.pipeline import deduplicate, extract, normalize, summary, verify


def references():
    return [
        r.model_dump() | {"record_type": r.metadata["record_type"]}
        for r in ingest_structured_documents()
    ]


def candidate(**changes):
    item = {
        "event_id": "evt-101",
        "email": " ADA.MENSAH@EXAMPLE.COM ",
        "full_name": "Ada   Mensah",
        "title": "Registration",
        "starts_at": "",
        "venue": "",
        "issues": [],
        "source_type": "email",
        "source_record_id": "1",
        "evidence": [
            {
                "source_type": "email",
                "source_reference": "https://mailtrap.io/example",
                "source_record_id": "1",
                "excerpt": "Name: Ada Mensah; Email: ada.mensah@example.com; EVT-101",
            }
        ],
    }
    item.update(changes)
    return item


def test_verified_identity_has_reference_and_provenance():
    result = verify(deduplicate(normalize([candidate()])), references(), "EVT-101")[0]
    assert result["status"] == "verified"
    assert result["email"] == "ada.mensah@example.com"
    assert {m["record_id"] for m in result["matches"]} == {"EVT-101", "P-001"}
    assert result["evidence"][0]["source_record_id"] == "1"


def test_inactive_and_not_registered_are_flagged():
    rows = [
        candidate(email="lindi.mokoena@example.com", full_name="Lindi Mokoena"),
        candidate(email="amina.patel@example.com", full_name="Amina Patel"),
    ]
    results = verify(deduplicate(normalize(rows)), references(), "EVT-101")
    assert "inactive_participant" in results[0]["issues"]
    assert "not_registered_for_event" in results[1]["issues"]
    assert all(r["status"] == "review_required" for r in results)


def test_duplicates_merge_evidence_and_detect_conflicts():
    other = candidate(full_name="Incorrect Name", source_record_id="2")
    other["evidence"] = deepcopy(other["evidence"])
    other["evidence"][0]["source_record_id"] = "2"
    rows = deduplicate(normalize([candidate(), other]))
    assert len(rows) == 1 and rows[0]["duplicate_count"] == 1
    assert len(rows[0]["evidence"]) == 2
    assert "conflicting_full_name" in rows[0]["issues"]
    assert verify(rows, references(), "EVT-101")[0]["status"] == "review_required"


def test_missing_event_is_not_inherited_from_run_target():
    result = verify(
        deduplicate(normalize([candidate(event_id="")])), references(), "EVT-101"
    )[0]
    assert result["event_id"] == "" and "missing_event_id" in result["issues"]
    assert result["status"] == "review_required"


def test_calendar_timezone_and_event_schedule_verification():
    ics = "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:test\r\nSUMMARY:AI Engineering Summit\r\nDESCRIPTION:EVT-101\r\nDTSTART:20261021T070000Z\r\nLOCATION:Cape Town Convention Centre\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
    sources = {
        "calendar": {
            "source_reference": "https://example.com/calendar.ics",
            "body": ics,
        }
    }
    rows = verify(deduplicate(normalize(extract(sources, 20))), references(), "EVT-101")
    assert rows[0]["status"] == "verified"
    assert rows[0]["starts_at"] == "2026-10-21T07:00:00+00:00"


def test_web_html_extracts_visible_claim_and_ignores_script():
    sources = {
        "web": {
            "source_reference": "https://example.com",
            "body": "<script>EVT-999</script><p>Name: Ada Mensah</p><p>Email: ada.mensah@example.com</p><p>EVT-101</p>",
        }
    }
    rows = extract(sources, 20)
    assert rows[0]["event_id"] == "EVT-101"
    assert rows[0]["full_name"] == "Ada Mensah"


def test_unknown_remote_holiday_is_not_falsely_verified():
    sources = {
        "web": {
            "source_reference": "https://date.nager.at",
            "body": '[{"name":"Holiday","date":"2026-01-01"}]',
        }
    }
    rows = verify(deduplicate(normalize(extract(sources, 20))), references(), "EVT-101")
    assert rows[0]["status"] == "review_required"
    assert summary(rows)["verified"] == 0


def test_multiple_ids_and_addresses_are_ambiguous():
    sources = {
        "email": {
            "source_reference": "https://mailtrap.io",
            "messages": [
                {
                    "id": "1",
                    "subject": "EVT-101 EVT-102",
                    "body": "ada@example.com theo@example.com",
                    "source_reference": "https://mailtrap.io/1",
                }
            ],
        }
    }
    row = extract(sources, 5)[0]
    assert not row["event_id"] and not row["email"]
    assert set(row["issues"]) == {"ambiguous_event_ids", "ambiguous_email_addresses"}


def test_controlled_mailtrap_email_expected_discrepancies_offline():
    root = Path(__file__).resolve().parents[2]
    sample = root / "docs/testing/mailtrap/evt101-registration"
    email = json.loads(sample.with_suffix(".json").read_text())
    assert email["text"] == sample.with_suffix(".txt").read_text()
    # Explicit synthetic unit input, never injected into a live run.
    sources = {
        "email": {
            "source_reference": "https://mailtrap.io/test-only",
            "messages": [
                {
                    "id": "1",
                    "subject": email["subject"],
                    "body": email["text"],
                    "source_reference": "https://mailtrap.io/test-only/1/body.txt",
                }
            ],
        }
    }
    row = verify(deduplicate(normalize(extract(sources, 1))), references(), "EVT-101")[
        0
    ]
    assert row["full_name"] == "Lindi Mokoena-Test"
    assert row["email"] == "lindi.mokoena@example.com"
    assert row["event_id"] == "EVT-101"
    assert row["status"] == "review_required"
    assert set(row["issues"]) == {"name_mismatch", "inactive_participant"}
    assert {match["record_id"] for match in row["matches"]} == {"EVT-101", "P-003"}
