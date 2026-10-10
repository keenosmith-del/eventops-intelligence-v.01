
from enum import StrEnum
from typing import Literal

from pydantic import Field

from app.models.domain import DomainModel


class ParticipantStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Policy(DomainModel):
    policy_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    rule_text: str = Field(min_length=1)


class DirectoryParticipant(DomainModel):
    participant_id: str = Field(min_length=1)
    full_name: str = Field(min_length=1)
    email: str = Field(min_length=1)
    organization: str = Field(min_length=1)
    status: ParticipantStatus
    registered_events: list[str] = Field(min_length=1)


class ParticipantDirectory(DomainModel):
    schema_version: Literal[1]
    directory_id: str = Field(min_length=1)
    participants: list[DirectoryParticipant] = Field(
        min_length=1
    )
