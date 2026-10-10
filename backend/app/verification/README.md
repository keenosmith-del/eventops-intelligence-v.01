# Deterministic verification

`pipeline.py` contains independently testable extraction, normalization, deduplication and comparison functions. Authority follows ADR-001: the indexed events.csv and directory.json records govern event details, active status and registration. External observations remain supporting evidence.

Results include normalized values, stable deterministic IDs, all source excerpts/references, duplicate counts, authoritative matches, explicit issues and verified/review_required status. Missing fields remain empty, ambiguous event/email references are flagged, and conflicting duplicate fields cannot become verified merely through merging. Name, schedule and venue comparisons are deterministic, not semantic model judgments.

Supported extraction is intentionally narrow and documented in the agent README; arbitrary attachments, OCR, general document understanding and fuzzy identity matching are not implemented. Positive verification tests use explicit synthetic claims matching the reference dataset. Default real public holiday sources have missing EVT IDs, so their actual records are flagged.
