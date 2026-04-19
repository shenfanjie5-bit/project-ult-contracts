"""Boundary tests for the contracts public entrypoints.

Two boundaries to enforce per ``contracts/CLAUDE.md``:

1. ``contracts`` must not depend on any business module — public.py is
   the high-traffic integration glue, so it's the most likely place to
   accidentally pull one in.
2. ``contracts.public`` must not pull in heavy runtime libraries
   (PostgreSQL/Iceberg/Neo4j/LLM). These would defeat the cheap
   importable-namespace promise that downstream modules rely on.
"""

from __future__ import annotations

import importlib
import sys


_BUSINESS_MODULES = (
    "data_platform",
    "main_core",
    "graph_engine",
    "audit_eval",        # consumer-direction only — contracts must not import it
    "entity_registry",
    "reasoner_runtime",
    "subsystem_sdk",
    "subsystem_announcement",
    "subsystem_news",
    "orchestrator",
    "assembly",
    "feature_store",
    "stream_layer",
)
_HEAVY_RUNTIME_PREFIXES = (
    "psycopg",
    "pyiceberg",
    "neo4j",
    "litellm",
    "openai",
    "anthropic",
    "torch",
    "tensorflow",
    "dagster",
)


def _fresh_import() -> None:
    """Force a fresh import of contracts.public to observe transitive deps.

    Critically only drop ``contracts.public`` itself — never the rest of the
    contracts package — so we don't reload schema modules out from under
    other tests in the same session that compare class identity with ``is``.
    """
    sys.modules.pop("contracts.public", None)
    importlib.import_module("contracts.public")


class TestNoBusinessModuleImports:
    def test_contracts_public_pulls_in_no_business_module(self) -> None:
        _fresh_import()

        offenders = sorted(
            mod
            for mod in sys.modules
            if any(mod == p or mod.startswith(p + ".") for p in _BUSINESS_MODULES)
        )

        assert not offenders, (
            f"contracts.public pulled in business module(s): {offenders}"
        )


class TestNoHeavyRuntimeImports:
    def test_contracts_public_pulls_in_no_heavy_runtime(self) -> None:
        _fresh_import()

        offenders = sorted(
            mod
            for mod in sys.modules
            if any(
                mod == p or mod.startswith(p + ".") for p in _HEAVY_RUNTIME_PREFIXES
            )
        )

        assert not offenders, (
            f"contracts.public pulled in heavy runtime module(s): {offenders}"
        )


class TestSmokeHookContractCoverage:
    """smoke_hook must continue to cover all four Ex payload families.

    If a future refactor drops one of Ex0/Ex1/Ex2/Ex3 from the smoke
    coverage, this test fails — guards against silent regression of the
    smoke contract.
    """

    def test_smoke_covers_four_ex_payload_models(self) -> None:
        from contracts import public

        result = public.smoke_hook.run(profile_id="lite-local")

        assert result["passed"], result.get("failure_reason")
        details = result.get("details", {})
        assert details.get("ex_models_checked") == 4, details
