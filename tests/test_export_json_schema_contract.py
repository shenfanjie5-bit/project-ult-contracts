from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from pydantic import BaseModel

import contracts.schemas as schemas
from contracts.core import ContractBaseModel, __version__
from contracts.export import (
    SCHEMA_MODEL_REGISTRY,
    SchemaArtifact,
    export_json_schemas,
    iter_schema_models,
)
from contracts.schemas import (
    FORBIDDEN_INGEST_METADATA_FIELDS,
    FORMAL_OBJECT_REGISTRY,
    Ex0Metadata,
    Ex1CandidateFact,
    Ex2CandidateSignal,
    Ex3CandidateGraphDelta,
    FormalObjectName,
)


EX_PAYLOAD_REQUIRED_FIELDS = {
    "ex0_metadata": {
        "subsystem_id",
        "version",
        "heartbeat_at",
        "status",
        "last_output_at",
        "pending_count",
    },
    "ex1_candidate_fact": {
        "fact_id",
        "entity_id",
        "fact_type",
        "fact_content",
        "confidence",
        "source_reference",
        "extracted_at",
        "subsystem_id",
    },
    "ex2_candidate_signal": {
        "signal_id",
        "signal_type",
        "direction",
        "magnitude",
        "affected_entities",
        "affected_sectors",
        "time_horizon",
        "evidence",
        "confidence",
        "subsystem_id",
    },
    "ex3_candidate_graph_delta": {
        "delta_id",
        "delta_type",
        "source_node",
        "target_node",
        "relation_type",
        "properties",
        "evidence",
        "subsystem_id",
    },
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_schema_artifact_is_a_valid_contract_model() -> None:
    artifact = SchemaArtifact(
        name="ex0_metadata",
        source_model="contracts.schemas.ex_payloads.Ex0Metadata",
        output_path="ex0_metadata.schema.json",
    )

    assert artifact.artifact_type == "json_schema"
    assert artifact.version == __version__ == "0.1.0"


def test_iter_schema_models_returns_stable_registry_order() -> None:
    assert tuple(iter_schema_models()) == tuple(SCHEMA_MODEL_REGISTRY.items())


def test_every_public_schema_pydantic_model_is_registered() -> None:
    public_schema_models = {
        name: exported
        for name in schemas.__all__
        if isinstance((exported := getattr(schemas, name)), type)
        and issubclass(exported, BaseModel)
    }

    registered_models = set(SCHEMA_MODEL_REGISTRY.values())
    missing_names = {
        name
        for name, model in public_schema_models.items()
        if model not in registered_models
    }

    assert not missing_names


def test_registry_contains_expected_schema_models_only_from_public_schemas() -> None:
    expected_models = {
        schemas.BaseExPayload,
        Ex0Metadata,
        Ex1CandidateFact,
        Ex2CandidateSignal,
        Ex3CandidateGraphDelta,
        schemas.CanonicalEntity,
        schemas.EntityAlias,
        schemas.EntityReference,
        schemas.ResolutionCase,
        schemas.ReasonerErrorClassification,
        schemas.ReasonerRequest,
        schemas.ReasonerResult,
        schemas.ReasonerReplay,
        schemas.ReasonerHealth,
        schemas.GraphSnapshot,
        schemas.GraphImpactSnapshot,
        schemas.AlphaResult,
        schemas.CycleMetadata,
        schemas.FormalObjectBase,
        *FORMAL_OBJECT_REGISTRY.values(),
    }

    assert set(SCHEMA_MODEL_REGISTRY.values()) == expected_models
    assert "backtest_result" not in SCHEMA_MODEL_REGISTRY


def test_export_writes_manifest_and_schema_files(tmp_path: Path) -> None:
    artifacts = export_json_schemas(tmp_path, version="0.1.0")
    manifest = load_json(tmp_path / "manifest.json")

    assert len(artifacts) == len(SCHEMA_MODEL_REGISTRY)
    assert manifest["artifact_type"] == "json_schema"
    assert manifest["version"] == "0.1.0"
    assert [artifact["name"] for artifact in manifest["artifacts"]] == list(
        SCHEMA_MODEL_REGISTRY
    )
    assert {path.name for path in tmp_path.glob("*.schema.json")} == {
        f"{name}.schema.json" for name in SCHEMA_MODEL_REGISTRY
    }


def test_exported_json_schemas_include_contract_metadata(tmp_path: Path) -> None:
    export_json_schemas(tmp_path, version="0.1.0")

    for name, model in iter_schema_models():
        schema = load_json(tmp_path / f"{name}.schema.json")

        assert schema["x-contract-version"] == "0.1.0"
        assert schema["x-source-model"] == (
            f"{model.__module__}.{model.__qualname__}"
        )


def test_exported_ex_payload_required_fields_match_contracts(tmp_path: Path) -> None:
    export_json_schemas(tmp_path, version="0.1.0")

    for schema_name, expected_required_fields in EX_PAYLOAD_REQUIRED_FIELDS.items():
        schema = load_json(tmp_path / f"{schema_name}.schema.json")

        assert set(schema["required"]) == expected_required_fields
        assert FORBIDDEN_INGEST_METADATA_FIELDS.isdisjoint(schema["properties"])


def test_exported_formal_object_set_is_closed(tmp_path: Path) -> None:
    export_json_schemas(tmp_path, version="0.1.0")

    concrete_formal_keys = {
        key
        for key, model in SCHEMA_MODEL_REGISTRY.items()
        if model in set(FORMAL_OBJECT_REGISTRY.values())
    }
    exported_text = "\n".join(
        path.name + "\n" + path.read_text(encoding="utf-8")
        for path in sorted(tmp_path.glob("*.json"))
    )

    assert concrete_formal_keys == {name.value for name in FormalObjectName}
    assert "backtest_result" not in exported_text
