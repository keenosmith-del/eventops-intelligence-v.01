"""Deterministic, conservative extraction and comparison. No model inference."""

import hashlib
import json
import re
import unicodedata
from copy import deepcopy
from datetime import date, datetime
from html.parser import HTMLParser

from icalendar import Calendar

EVENT = re.compile(r"\bEVT-\d+\b", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")


def text(value) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value or ""))).strip()


def claim(body: str) -> dict:
    event_ids = sorted(set(x.upper() for x in EVENT.findall(body)))
    emails = sorted(set(x.casefold() for x in EMAIL.findall(body)))
    name = re.search(r"(?:full[ _]?name|name)\s*:\s*([^\n;]+)", body, re.I)
    issues = []
    if len(event_ids) > 1:
        issues.append("ambiguous_event_ids")
    if len(emails) > 1:
        issues.append("ambiguous_email_addresses")
    return {
        "event_id": event_ids[0] if len(event_ids) == 1 else "",
        "email": emails[0] if len(emails) == 1 else "",
        "full_name": name.group(1) if name else "",
        "issues": issues,
    }


def source_record(
    item: dict, source: str, reference: str, source_id: str, excerpt: str
) -> dict:
    return {
        **item,
        "source_type": source,
        "source_record_id": source_id,
        "evidence": [
            {
                "source_type": source,
                "source_reference": reference,
                "source_record_id": source_id,
                "excerpt": excerpt[:1600],
            }
        ],
    }


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def extract(sources: dict, limit: int, year: int = 2026) -> list[dict]:
    records = []
    for source, payload in sources.items():
        reference = payload["source_reference"]
        if source == "calendar":
            calendar = Calendar.from_ical(payload["body"])
            for component in calendar.walk("VEVENT"):
                start = component.get("DTSTART")
                start = start.dt if start else None
                if isinstance(start, (datetime, date)) and start.year != year:
                    continue
                summary = str(component.get("SUMMARY", ""))
                description = str(component.get("DESCRIPTION", ""))
                item = claim(summary + "\n" + description)
                item.update(
                    title=summary,
                    starts_at=start.isoformat() if start else "",
                    venue=str(component.get("LOCATION", "")),
                )
                uid = (
                    str(component.get("UID", ""))
                    or hashlib.sha256((summary + str(start)).encode()).hexdigest()[:16]
                )
                records.append(
                    source_record(
                        item, source, reference, uid, summary + "\n" + description
                    )
                )
                if sum(r["source_type"] == source for r in records) >= limit:
                    break
        elif source == "email":
            for message in payload["messages"][:limit]:
                body = message["subject"] + "\n" + message["body"]
                item = claim(body)
                item["title"] = message["subject"]
                records.append(
                    source_record(
                        item, source, message["source_reference"], message["id"], body
                    )
                )
        else:
            body = payload["body"]
            try:
                items = json.loads(body)
            except ValueError:
                parser = VisibleText()
                parser.feed(body)
                visible = "\n".join(parser.parts)
                items = [
                    {
                        **claim(visible),
                        "title": "Web page observation",
                        "excerpt": visible[:1600],
                    }
                ]
            if isinstance(items, dict):
                items = items.get("records", [items])
            if not isinstance(items, list):
                raise ValueError(
                    "Web source must be a JSON object/list or readable HTML."
                )
            for index, item in enumerate(items[:limit]):
                if not isinstance(item, dict):
                    raise ValueError("Web records must be objects.")
                mapped = {
                    k: item.get(k, "")
                    for k in [
                        "event_id",
                        "full_name",
                        "email",
                        "title",
                        "starts_at",
                        "venue",
                    ]
                }
                mapped["title"] = (
                    mapped["title"]
                    or item.get("name")
                    or item.get("localName")
                    or "Web observation"
                )
                mapped["starts_at"] = mapped["starts_at"] or item.get("date", "")
                mapped["issues"] = item.get("issues", [])
                records.append(
                    source_record(
                        mapped,
                        source,
                        reference,
                        str(item.get("id", index)),
                        str(item.get("excerpt", json.dumps(item, ensure_ascii=False))),
                    )
                )
    return records


def normalize(records: list[dict]) -> list[dict]:
    normalized = []
    for raw in records:
        record = deepcopy(raw)
        for key in ["title", "full_name", "email", "event_id", "starts_at", "venue"]:
            record[key] = text(record.get(key, ""))[:500]
        record["event_id"] = record["event_id"].upper()
        record["email"] = record["email"].casefold()
        record["title"] = re.sub(r"^South Africa:\s*", "", record["title"], flags=re.I)
        record["issues"] = list(record.get("issues", []))
        if record["email"] and not EMAIL.fullmatch(record["email"]):
            record["issues"].append("invalid_email")
        if record["starts_at"]:
            try:
                start = datetime.fromisoformat(
                    record["starts_at"].replace("Z", "+00:00")
                )
                if len(record["starts_at"]) > 10 and start.utcoffset() is None:
                    record["issues"].append("missing_timezone")
                record["starts_at"] = (
                    start.isoformat()
                    if len(record["starts_at"]) > 10
                    else record["starts_at"]
                )
            except ValueError:
                record["issues"].append("invalid_timestamp")
        normalized.append(record)
    return normalized


def deduplicate(records: list[dict]) -> list[dict]:
    merged = {}
    for record in records:
        key = (
            (record["event_id"], record["email"])
            if record["email"]
            else (
                record["event_id"],
                record["title"].casefold(),
                record["starts_at"][:10],
            )
        )
        if not any(key):
            key = (record["source_type"], record["source_record_id"])
        if key not in merged:
            merged[key] = deepcopy(record)
            merged[key]["duplicate_count"] = 0
        else:
            existing = merged[key]
            existing["duplicate_count"] += 1
            existing["evidence"].extend(record["evidence"])
            existing["issues"].extend(record["issues"])
            for field in ["full_name", "venue", "starts_at"]:
                if (
                    existing[field]
                    and record[field]
                    and existing[field].casefold() != record[field].casefold()
                ):
                    existing["issues"].append(f"conflicting_{field}")
                elif not existing[field]:
                    existing[field] = record[field]
    for key, record in merged.items():
        record["id"] = hashlib.sha256(json.dumps(key).encode()).hexdigest()[:16]
        record["issues"] = sorted(set(record["issues"]))
    return list(merged.values())


def reference_fields(record):
    content = record["content"]

    def field(pattern):
        match = re.search(pattern, content)
        return match.group(1).strip() if match else ""

    if record["record_type"] == "participant":
        return {
            "full_name": field(r"^Participant [^:]+: (.*?)\. Email:"),
            "email": field(r"Email: (.*?)\. Organization:"),
            "status": record["metadata"].get("participant_status", ""),
            "event_ids": record["metadata"].get("event_ids", "").split(","),
        }
    return {
        "title": field(r"^Event [^:]+: (.*?)\. Starts at:"),
        "starts_at": field(r"Starts at: (.*?)\. Ends at:"),
        "venue": field(r"Venue: (.*?)\. Capacity:"),
    }


def verify(
    records: list[dict], references: list[dict], target_event: str
) -> list[dict]:
    events = {r["record_id"]: r for r in references if r["record_type"] == "event"}
    people = {
        reference_fields(r)["email"].casefold(): r
        for r in references
        if r["record_type"] == "participant"
    }
    results = []
    for candidate in records:
        record = deepcopy(candidate)
        issues = record["issues"]
        matches, checks = [], []

        def check(rule, field, actual, expected, passed, issue=None):
            checks.append({
                "rule": rule, "field": field, "actual": actual,
                "reference": expected, "status": "passed" if passed else "failed",
            })
            if not passed and issue:
                issues.append(issue)

        for issue in list(issues):
            checks.append({"rule": issue, "field": "source", "actual": issue,
                           "reference": None, "status": "failed"})
        event = events.get(record["event_id"])
        check("event_reference", "event_id", record["event_id"],
              event["record_id"] if event else None, bool(event),
              "missing_event_id" if not record["event_id"] else "unknown_event_id")
        if event:
            check("target_event", "event_id", record["event_id"], target_event,
                  record["event_id"] == target_event, "different_target_event")
            fields = reference_fields(event)
            matches.append({
                "record_id": event["record_id"],
                "source_reference": event["metadata"]["source_reference"],
                "content": event["content"], "fields": fields,
            })
            if record["email"]:
                person = people.get(record["email"])
                check("directory_identity", "email", record["email"],
                      reference_fields(person)["email"] if person else None,
                      bool(person), "participant_not_in_directory")
                if person:
                    pf = reference_fields(person)
                    matches.append({
                        "record_id": person["record_id"],
                        "source_reference": person["metadata"]["source_reference"],
                        "content": person["content"], "fields": pf,
                    })
                    check("active_participant", "status", pf["status"], "active",
                          pf["status"] == "active", "inactive_participant")
                    check("event_registration", "event_id", record["event_id"],
                          pf["event_ids"], record["event_id"] in pf["event_ids"],
                          "not_registered_for_event")
                    check("participant_name", "full_name", record["full_name"],
                          pf["full_name"], bool(record["full_name"]) and
                          record["full_name"].casefold() == pf["full_name"].casefold(),
                          "missing_full_name" if not record["full_name"] else "name_mismatch")
            else:
                if record["source_type"] == "email":
                    check("email_required", "email", "", None, False, "missing_email")
                for field in ["title", "starts_at", "venue"]:
                    if not record[field]:
                        check("event_" + field, field, record[field], fields[field],
                              False, "missing_" + field)
                    elif field == "starts_at":
                        try:
                            passed = datetime.fromisoformat(record[field]) == datetime.fromisoformat(fields[field])
                            issue = "schedule_mismatch"
                        except ValueError:
                            passed, issue = False, "invalid_timestamp"
                        check("event_schedule", field, record[field], fields[field], passed, issue)
                    else:
                        check("event_" + field, field, record[field], fields[field],
                              record[field].casefold() == fields[field].casefold(), field + "_mismatch")
        record["issues"] = sorted(set(issues))
        record["matches"] = matches
        record["checks"] = checks
        record["status"] = "verified" if matches and not record["issues"] else "review_required"
        results.append(record)
    return results


def summary(records):
    return {
        "total": len(records),
        "verified": sum(r["status"] == "verified" for r in records),
        "flagged": sum(r["status"] != "verified" for r in records),
        "duplicates_merged": sum(r.get("duplicate_count", 0) for r in records),
    }
