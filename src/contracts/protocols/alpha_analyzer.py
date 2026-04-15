"""AlphaAnalyzer protocol definition."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from contracts.core import EntityId
from contracts.schemas.alpha import AlphaResult


@runtime_checkable
class AlphaAnalyzer(Protocol):
    """Shared interface for all alpha analyzers."""

    @property
    def analyzer_name(self) -> str:
        """Stable analyzer implementation name."""

        ...

    @property
    def analyzer_version(self) -> str:
        """Analyzer implementation version."""

        ...

    def analyze(self, stock: EntityId, context: Mapping[str, object]) -> AlphaResult:
        """Analyze one stock entity within the provided context."""

        ...


__all__ = ["AlphaAnalyzer"]
