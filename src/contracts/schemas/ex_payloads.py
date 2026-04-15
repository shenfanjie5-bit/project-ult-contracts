"""Ex payload schemas shared by producer-facing contracts."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from pydantic import Field, ValidationInfo, field_validator, model_validator

from contracts.core import (
    Confidence,
    ContractBaseModel,
    DeltaId,
    Direction,
    EntityId,
    EvidenceRef,
    FactId,
    HeartbeatStatus,
    Magnitude,
    NodeId,
    SignalId,
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
    pending_count: int = Field(ge=0, strict=True)

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


class Ex1CandidateFact(BaseExPayload):
    """Ex-1 candidate fact payload."""

    fact_id: FactId
    entity_id: EntityId
    fact_type: str = Field(min_length=1)
    fact_content: dict[str, object]
    confidence: Confidence
    source_reference: dict[str, object]
    extracted_at: datetime

    @field_validator("fact_content", "source_reference")
    @classmethod
    def validate_non_empty_dict(
        cls, value: dict[str, object], info: ValidationInfo
    ) -> dict[str, object]:
        """Reject empty structured payload fields."""

        if not value:
            raise ValueError(f"{info.field_name} must not be empty")

        return value

    @field_validator("extracted_at")
    @classmethod
    def validate_extracted_at_timezone(cls, extracted_at: datetime) -> datetime:
        """Require timezone-aware extraction timestamps."""

        if (
            extracted_at.tzinfo is None
            or extracted_at.tzinfo.utcoffset(extracted_at) is None
        ):
            raise ValueError("extracted_at must be timezone-aware")

        return extracted_at


class Ex2CandidateSignal(BaseExPayload):
    """Ex-2 candidate signal payload."""

    signal_id: SignalId
    signal_type: str = Field(min_length=1)
    direction: Direction
    magnitude: Magnitude
    affected_entities: list[EntityId] = Field(min_length=1)
    affected_sectors: list[str] = Field(min_length=1)
    time_horizon: str = Field(min_length=1)
    evidence: list[EvidenceRef] = Field(min_length=1)
    confidence: Confidence


class Ex3CandidateGraphDelta(BaseExPayload):
    """Ex-3 candidate graph delta payload."""

    delta_id: DeltaId
    delta_type: str = Field(min_length=1)
    source_node: NodeId
    target_node: NodeId
    relation_type: str = Field(min_length=1)
    properties: dict[str, object]
    evidence: list[EvidenceRef] = Field(min_length=1)


__all__ = [
    "FORBIDDEN_INGEST_METADATA_FIELDS",
    "BaseExPayload",
    "Ex0Metadata",
    "Ex1CandidateFact",
    "Ex2CandidateSignal",
    "Ex3CandidateGraphDelta",
]
