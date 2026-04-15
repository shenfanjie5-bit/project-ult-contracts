"""Cycle 控制元数据 Schema。"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Self

from pydantic import field_validator, model_validator

from contracts.core import ContractBaseModel, CycleId, VersionString, __version__


class CyclePhase(str, Enum):
    """Cycle 执行阶段。"""

    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    PUBLISHING = "publishing"
    COMPLETED = "completed"
    FAILED = "failed"


class CycleMetadata(ContractBaseModel):
    """最小 cycle 控制元数据。"""

    cycle_id: CycleId
    phase: CyclePhase
    started_at: datetime
    ended_at: datetime | None = None
    previous_cycle_id: CycleId | None = None
    version: VersionString = __version__

    @field_validator("started_at", "ended_at")
    @classmethod
    def datetime_must_be_timezone_aware(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """确保 cycle 时间字段包含时区信息。"""
        if value is None:
            return value
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            raise ValueError("cycle datetime fields must be timezone-aware")
        return value

    @model_validator(mode="after")
    def ended_at_must_not_precede_started_at(self) -> Self:
        """确保结束时间不早于开始时间。"""
        if self.ended_at is not None and self.ended_at < self.started_at:
            raise ValueError("ended_at must be greater than or equal to started_at")
        return self


__all__ = ["CyclePhase", "CycleMetadata"]
