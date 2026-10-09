
from datetime import datetime, timezone
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DomainModel(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )


class SourceType(StrEnum):
    STRUCTURED = "structured"
    CALENDAR = "calendar"
    EMAIL = "email"
    WEB = "web"


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    REVIEW_REQUIRED = "review_required"


class AgentRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEW_REQUIRED = "review_required"


class Event(DomainModel):
    event_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    starts_at: datetime
    ends_at: datetime
    venue: str = Field(min_length=1)
    capacity: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_schedule(self) -> Self:
        if (
            self.starts_at.utcoffset() is None
            or self.ends_at.utcoffset() is None
        ):
            raise ValueError("Event timestamps must include a timezone")

        if self.ends_at <= self.starts_at:
            raise ValueError("Event must end after it starts")

        return self


class Registration(DomainModel):
    registration_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    full_name: str | None = None
    email: str | None = None
    organization: str | None = None
    source_evidence_ids: list[str] = Field(default_factory=list)


class KnowledgeRecord(DomainModel):
    document_id: str = Field(min_length=1)
    record_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    event_id: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class SourceEvidence(DomainModel):
    evidence_id: str = Field(min_length=1)
    source_type: SourceType
    source_reference: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    excerpt: str | None = None
    observed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class AgentRun(DomainModel):
    run_id: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    status: AgentRunStatus = AgentRunStatus.PENDING
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    finished_at: datetime | None = None


class VerificationResult(DomainModel):
    registration_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    status: VerificationStatus
    evidence_ids: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_verified_result(self) -> Self:
        if self.status == VerificationStatus.VERIFIED:
            if not self.evidence_ids:
                raise ValueError(
                    "Verified results must reference evidence"
                )

            if self.issues:
                raise ValueError(
                    "Verified results cannot have unresolved issues"
                )

        return self
