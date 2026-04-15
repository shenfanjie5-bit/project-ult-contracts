"""DataSourceAdapter protocol definition."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import Field

from contracts.core import ContractBaseModel
from contracts.schemas.cycle import CycleMetadata
from contracts.schemas.ex_payloads import (
    Ex0Metadata,
    Ex1CandidateFact,
    Ex2CandidateSignal,
    Ex3CandidateGraphDelta,
)


class DataSourceBatch(ContractBaseModel):
    """Collected Ex payloads for one cycle."""

    metadata: Ex0Metadata
    facts: list[Ex1CandidateFact] = Field(default_factory=list)
    signals: list[Ex2CandidateSignal] = Field(default_factory=list)
    graph_deltas: list[Ex3CandidateGraphDelta] = Field(default_factory=list)


@runtime_checkable
class DataSourceAdapter(Protocol):
    """Shared interface for producer-side data source adapters."""

    @property
    def adapter_name(self) -> str:
        """Stable adapter implementation name."""

        ...

    @property
    def adapter_version(self) -> str:
        """Adapter implementation version."""

        ...

    def collect(self, cycle: CycleMetadata) -> DataSourceBatch:
        """Collect Ex payloads for one orchestrator cycle."""

        ...


__all__ = ["DataSourceAdapter", "DataSourceBatch"]
