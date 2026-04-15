from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import cast

import pytest
from pydantic import BaseModel, ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from contracts.errors import ContractError, ErrorCode
from contracts.export import SCHEMA_MODEL_REGISTRY, export_json_schemas
from contracts.schemas import (
    FORBIDDEN_INGEST_METADATA_FIELDS,
    FORMAL_OBJECT_NAMES,
    get_formal_object_model,
)


MANIFEST_PATH = PROJECT_ROOT / "fixtures" / "manifest.json"
EX_SCHEMA_NAMES = frozenset(
    {
        "ex0_metadata",
        "ex1_candidate_fact",
        "ex2_candidate_signal",
        "ex3_candidate_graph_delta",
    }
)
FORMAL_OBJECT_SCHEMA_NAMES = frozenset(name.value for name in FORMAL_OBJECT_NAMES)


def load_fixture(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return cast(dict[str, object], data)


def resolve_model(import_path: str) -> type[BaseModel]:
    module_name, model_name = import_path.rsplit(".", maxsplit=1)
    model = getattr(importlib.import_module(module_name), model_name)

    assert isinstance(model, type)
    assert issubclass(model, BaseModel)
    return model


def manifest_entries() -> list[dict[str, object]]:
    manifest = load_fixture(MANIFEST_PATH)
    fixtures = manifest["fixtures"]

    assert manifest["version"] == "0.1.0"
    assert isinstance(fixtures, list)
    assert all(isinstance(entry, dict) for entry in fixtures)

    return cast(list[dict[str, object]], fixtures)


def entries_by_validity(valid: bool) -> list[dict[str, object]]:
    return [entry for entry in manifest_entries() if entry["valid"] is valid]


def entry_path(entry: dict[str, object]) -> Path:
    return PROJECT_ROOT / str(entry["path"])


def entry_id(entry: dict[str, object]) -> str:
    return str(entry["path"])


@pytest.mark.parametrize(
    "path",
    sorted((PROJECT_ROOT / "fixtures").rglob("*.json")),
    ids=lambda path: str(path.relative_to(PROJECT_ROOT)),
)
def test_fixture_json_files_are_standard_json(path: Path) -> None:
    load_fixture(path)


def test_manifest_shape_and_paths_are_valid() -> None:
    required_keys = {"path", "model", "schema_name", "valid", "consumer"}
    seen_paths: set[str] = set()

    for entry in manifest_entries():
        assert required_keys.issubset(entry)
        assert str(entry["path"]) not in seen_paths
        seen_paths.add(str(entry["path"]))

        assert entry_path(entry).is_file()
        assert isinstance(entry["model"], str)
        assert isinstance(entry["schema_name"], str)
        assert isinstance(entry["valid"], bool)
        assert isinstance(entry["consumer"], list)
        assert entry["consumer"]
        assert all(isinstance(consumer, str) for consumer in entry["consumer"])

        resolve_model(str(entry["model"]))
        if entry["valid"] is False:
            assert "expected_error" in entry


def test_valid_fixture_schema_names_match_export_registry() -> None:
    for entry in entries_by_validity(True):
        schema_name = str(entry["schema_name"])
        model = resolve_model(str(entry["model"]))

        assert schema_name in SCHEMA_MODEL_REGISTRY
        assert SCHEMA_MODEL_REGISTRY[schema_name] is model


@pytest.mark.parametrize(
    "entry",
    entries_by_validity(True),
    ids=entry_id,
)
def test_valid_fixtures_validate_against_declared_models(
    entry: dict[str, object],
) -> None:
    model = resolve_model(str(entry["model"]))
    payload = load_fixture(entry_path(entry))

    instance = model.model_validate(payload)

    assert isinstance(instance, model)


@pytest.mark.parametrize(
    "entry",
    entries_by_validity(False),
    ids=entry_id,
)
def test_invalid_fixtures_fail_with_expected_error(
    entry: dict[str, object],
) -> None:
    expected_error = str(entry["expected_error"])
    payload = load_fixture(entry_path(entry))

    if expected_error == ErrorCode.UNKNOWN_FORMAL_OBJECT.value:
        assert payload["object_name"] == "backtest_result"
        with pytest.raises(ContractError) as exc_info:
            get_formal_object_model(str(payload["object_name"]))

        assert exc_info.value.code is ErrorCode.UNKNOWN_FORMAL_OBJECT
        assert exc_info.value.details == {"object_name": "backtest_result"}
        return

    assert expected_error == "ValidationError"
    model = resolve_model(str(entry["model"]))
    with pytest.raises(ValidationError) as exc_info:
        model.model_validate(payload)

    case = str(entry["case"])
    if "forbidden-ingest-metadata" in case:
        assert FORBIDDEN_INGEST_METADATA_FIELDS.intersection(payload)
        assert "ingest metadata" in str(exc_info.value)
    elif "missing-required" in case:
        assert any(error["type"] == "missing" for error in exc_info.value.errors())
    elif "ended-at-before-started-at" in case:
        assert "ended_at" in str(exc_info.value)
    elif "wrong-zone" in case:
        assert "zone" in str(exc_info.value)


def test_valid_ex_fixtures_exclude_ingest_metadata_fields() -> None:
    assert FORBIDDEN_INGEST_METADATA_FIELDS == frozenset(
        {"submitted_at", "ingest_seq"}
    )

    for entry in entries_by_validity(True):
        if entry["schema_name"] in EX_SCHEMA_NAMES:
            payload = load_fixture(entry_path(entry))

            assert FORBIDDEN_INGEST_METADATA_FIELDS.isdisjoint(payload)


def test_valid_formal_object_fixtures_match_closed_registry() -> None:
    formal_entries = [
        entry
        for entry in entries_by_validity(True)
        if entry["schema_name"] in FORMAL_OBJECT_SCHEMA_NAMES
    ]
    object_names = set()

    assert len(formal_entries) == 8
    for entry in formal_entries:
        model = resolve_model(str(entry["model"]))
        payload = load_fixture(entry_path(entry))
        instance = model.model_validate(payload)

        object_names.add(instance.object_name)

    assert object_names == set(FORMAL_OBJECT_NAMES)


def test_backtest_result_only_appears_as_invalid_fixture() -> None:
    fixture_paths = []

    for entry in manifest_entries():
        payload_text = json.dumps(load_fixture(entry_path(entry)), sort_keys=True)
        if "backtest_result" in payload_text:
            assert entry["valid"] is False
            fixture_paths.append(str(entry["path"]))

    assert fixture_paths == [
        "fixtures/invalid/formal_objects/unknown_backtest_result.json"
    ]


def test_exported_schema_set_covers_all_valid_fixture_schema_names(
    tmp_path: Path,
) -> None:
    exported_artifacts = export_json_schemas(tmp_path, version="0.1.0")
    exported_names = {artifact.name for artifact in exported_artifacts}
    valid_schema_names = {
        str(entry["schema_name"]) for entry in entries_by_validity(True)
    }

    assert valid_schema_names <= exported_names
    for schema_name in valid_schema_names:
        assert (tmp_path / f"{schema_name}.schema.json").is_file()
