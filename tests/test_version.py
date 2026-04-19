from __future__ import annotations

import importlib
import pathlib
import sys
import tomllib

import pydantic
import pytest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"


@pytest.fixture()
def contracts_modules() -> tuple[object, object]:
    sys.path.insert(0, str(SRC_DIR))
    try:
        contracts = importlib.import_module("contracts")
        core = importlib.import_module("contracts.core")
    finally:
        sys.path.remove(str(SRC_DIR))

    return contracts, core


def test_contract_version_entry_is_reexported_from_core(
    contracts_modules: tuple[object, object],
) -> None:
    contracts, core = contracts_modules

    assert contracts.__version__ == "0.1.2"
    assert core.__version__ == "0.1.2"
    assert core.CURRENT_VERSION_ENTRY.version == contracts.__version__
    assert core.CURRENT_VERSION_ENTRY.compatibility_note == (
        "新增 contracts.public 集成入口（health_probe / smoke_hook / "
        "init_hook / version_declaration / cli），向后兼容；不引入新业务字段"
    )
    assert core.CURRENT_VERSION_ENTRY.breaking is False


def test_contract_version_entry_released_at_must_be_valid_datetime(
    contracts_modules: tuple[object, object],
) -> None:
    _, core = contracts_modules

    with pytest.raises(pydantic.ValidationError):
        core.ContractVersionEntry(version="0.2.0", released_at="not-a-date")


@pytest.mark.parametrize("version", ["", "not-a-version", "0.1", "0.1.0-dev"])
def test_contract_version_entry_version_must_be_semantic(
    contracts_modules: tuple[object, object],
    version: str,
) -> None:
    _, core = contracts_modules

    with pytest.raises(pydantic.ValidationError):
        core.ContractVersionEntry(version=version, released_at="2026-04-15T00:00:00Z")


def test_contract_version_entry_released_at_must_be_timezone_aware(
    contracts_modules: tuple[object, object],
) -> None:
    _, core = contracts_modules

    assert core.CURRENT_VERSION_ENTRY.released_at.tzinfo is not None

    with pytest.raises(pydantic.ValidationError):
        core.ContractVersionEntry(version="0.2.0", released_at="2026-04-15T00:00:00")


def test_pyproject_version_matches_contract_version(
    contracts_modules: tuple[object, object],
) -> None:
    contracts, _ = contracts_modules
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["version"] == contracts.__version__ == "0.1.2"


def test_changelog_contains_initial_version_record() -> None:
    changelog = (PROJECT_ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")

    assert "0.1.0" in changelog
    assert "2026-04-15" in changelog
