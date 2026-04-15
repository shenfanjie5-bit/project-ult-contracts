"""Cycle control metadata schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Self

from pydantic import field_validator, model_validator

from contracts.core import ContractBaseModel, CycleId, VersionString, __version__


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

    @field_validator("started_at", "ended_at")
    @classmethod
    def validate_timezone_aware(cls, value: datetime | None) -> datetime | None:
        """Require timezone-aware cycle timestamps."""

        if value is None:
            return value

        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("cycle timestamps must be timezone-aware")

        return value

    @model_validator(mode="after")
    def validate_ended_at_order(self) -> Self:
        """Ensure a finished cycle does not end before it starts."""

        if self.ended_at is not None and self.ended_at < self.started_at:
            raise ValueError("ended_at must be greater than or equal to started_at")

        return self


__all__ = ["CyclePhase", "CycleMetadata"]
