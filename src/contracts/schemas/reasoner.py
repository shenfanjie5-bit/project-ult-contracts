"""Reasoner runtime shared schemas."""

from __future__ import annotations

from enum import Enum

from pydantic import Field

from contracts.core import (
    AwareDatetime,
    Confidence,
    ContractBaseModel,
    CycleId,
    EvidenceRef,
    HeartbeatStatus,
    Severity,
    SubsystemId,
    VersionString,
)
from contracts.core.types import NonEmptyString


class ReasonerStatus(str, Enum):
    """Stable status values for reasoner request execution."""

    ACCEPTED = "accepted"
    COMPLETED = "completed"
    FAILED = "failed"


class ReasonerErrorCategory(str, Enum):
    """Public reasoner error buckets shared across runtime consumers."""

    INPUT_CONTRACT = "input_contract"
    MODEL_PROVIDER = "model_provider"
    TOOL_EXECUTION = "tool_execution"
    TIMEOUT = "timeout"
    INTERNAL = "internal"


class ReasonerErrorClassification(ContractBaseModel):
    """Normalized reasoner-runtime error classification."""

    category: ReasonerErrorCategory
    severity: Severity
    retryable: bool
    message: NonEmptyString
    details: dict[str, object] = Field(default_factory=dict)


class ReasonerRequest(ContractBaseModel):
    """Request envelope accepted by reasoner-runtime."""

    request_id: NonEmptyString
    cycle_id: CycleId
    reasoner_name: NonEmptyString
    reasoner_version: VersionString
    prompt: NonEmptyString
    context: dict[str, object]
    requested_at: AwareDatetime
    input_refs: list[EvidenceRef] = Field(default_factory=list)


class ReasonerResult(ContractBaseModel):
    """Result envelope returned by reasoner-runtime."""

    result_id: NonEmptyString
    request_id: NonEmptyString
    status: ReasonerStatus
    reasoner_name: NonEmptyString
    reasoner_version: VersionString
    output: dict[str, object]
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    completed_at: AwareDatetime
    confidence: Confidence | None = None
    error_classification: ReasonerErrorClassification | None = None


class ReasonerReplay(ContractBaseModel):
    """Replay bundle for deterministic reasoner-runtime inspection."""

    replay_id: NonEmptyString
    request: ReasonerRequest
    result: ReasonerResult
    recorded_at: AwareDatetime
    replay_version: VersionString


class ReasonerHealth(ContractBaseModel):
    """Reasoner-runtime health contract."""

    subsystem_id: SubsystemId
    version: VersionString
    checked_at: AwareDatetime
    status: HeartbeatStatus
    last_success_at: AwareDatetime | None
    pending_count: int = Field(ge=0, strict=True)
    error_classification: ReasonerErrorClassification | None = None


__all__ = [
    "ReasonerStatus",
    "ReasonerErrorCategory",
    "ReasonerErrorClassification",
    "ReasonerRequest",
    "ReasonerResult",
    "ReasonerReplay",
    "ReasonerHealth",
]
