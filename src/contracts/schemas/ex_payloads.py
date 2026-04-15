"""Ex payload schemas shared by producer-facing contracts."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from pydantic import Field, field_validator, model_validator

from contracts.core import (
    ContractBaseModel,
    HeartbeatStatus,
    SubsystemId,
    VersionString,
)


FORBIDDEN_INGEST_METADATA_FIELDS: frozenset[str] = frozenset(
    {"submitted_at", "ingest_seq"}
)


class BaseExPayload(ContractBaseModel):
    """Shared base for Ex producer payload schemas."""

    subsystem_id: SubsystemId

    @model_validator(mode="before")
    @classmethod
    def reject_ingest_metadata(cls, data: object) -> object:
        """Reject Layer B ingest metadata in producer payloads."""

        if isinstance(data, Mapping):
            forbidden_fields = FORBIDDEN_INGEST_METADATA_FIELDS.intersection(data)
            if forbidden_fields:
                field_list = ", ".join(sorted(forbidden_fields))
                raise ValueError(
                    f"ingest metadata fields are not allowed in Ex payloads: "
                    f"{field_list}"
                )

        return data


class Ex0Metadata(BaseExPayload):
    """Ex-0 metadata and heartbeat payload."""

    version: VersionString
    heartbeat_at: datetime
    status: HeartbeatStatus
    last_output_at: datetime | None
    pending_count: int = Field(ge=0)

    @field_validator("heartbeat_at")
    @classmethod
    def validate_heartbeat_at_timezone(cls, heartbeat_at: datetime) -> datetime:
        """Require timezone-aware heartbeat timestamps."""

        if (
            heartbeat_at.tzinfo is None
            or heartbeat_at.tzinfo.utcoffset(heartbeat_at) is None
        ):
            raise ValueError("heartbeat_at must be timezone-aware")

        return heartbeat_at

    @field_validator("last_output_at")
    @classmethod
    def validate_last_output_at_timezone(
        cls, last_output_at: datetime | None
    ) -> datetime | None:
        """Require timezone-aware output timestamps when present."""

        if last_output_at is None:
            return None

        if (
            last_output_at.tzinfo is None
            or last_output_at.tzinfo.utcoffset(last_output_at) is None
        ):
            raise ValueError("last_output_at must be timezone-aware")

        return last_output_at


__all__ = [
    "FORBIDDEN_INGEST_METADATA_FIELDS",
    "BaseExPayload",
    "Ex0Metadata",
]
