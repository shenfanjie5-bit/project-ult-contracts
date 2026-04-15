"""Cycle control metadata schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import TypeAdapter, field_validator, model_validator

from contracts.core import ContractBaseModel, CycleId, VersionString, __version__


_DATETIME_ADAPTER = TypeAdapter(datetime)


class CyclePhase(str, Enum):
    """Lifecycle phase for a control cycle."""

    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    PUBLISHING = "publishing"
    COMPLETED = "completed"
    FAILED = "failed"


class CycleMetadata(ContractBaseModel):
    """Minimal metadata that identifies and times a control cycle."""

    cycle_id: CycleId
    phase: CyclePhase
    started_at: datetime
    ended_at: datetime | None = None
    previous_cycle_id: CycleId | None = None
    version: VersionString = __version__

    @model_validator(mode="before")
    @classmethod
    def validate_ended_at_order(cls, data: Any) -> Any:
        """Reject impossible cycle timing before assignment mutates the model."""

        if not isinstance(data, dict):
            return data

        started_at = data.get("started_at")
        ended_at = data.get("ended_at")

        if started_at is None or ended_at is None:
            return data

        parsed_started_at = cls._datetime_for_ordering(started_at)
        parsed_ended_at = cls._datetime_for_ordering(ended_at)

        if parsed_started_at is None or parsed_ended_at is None:
            return data

        if parsed_ended_at < parsed_started_at:
            raise ValueError("ended_at must be greater than or equal to started_at")

        return data

    @field_validator("started_at", "ended_at")
    @classmethod
    def validate_timezone_aware(cls, value: datetime | None) -> datetime | None:
        """Require timezone-aware cycle timestamps."""

        if value is None:
            return value

        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("cycle timestamps must be timezone-aware")

        return value

    @staticmethod
    def _datetime_for_ordering(value: Any) -> datetime | None:
        try:
            parsed = _DATETIME_ADAPTER.validate_python(value)
        except ValueError:
            return None

        if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
            return None

        return parsed


__all__ = ["CyclePhase", "CycleMetadata"]
