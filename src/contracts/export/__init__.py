"""JSON Schema 自动导出 CLI 与库入口。"""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Literal

from contracts.core import ContractBaseModel, VersionString, __version__
from contracts.schemas import (
    AlphaResult,
    AlphaResultSnapshot,
    AuditRecord,
    BaseExPayload,
    CycleMetadata,
    DashboardSnapshot,
    Ex0Metadata,
    Ex1CandidateFact,
    Ex2CandidateSignal,
    Ex3CandidateGraphDelta,
    FormalObjectBase,
    OfficialAlphaPool,
    RecommendationSnapshot,
    ReplayRecord,
    Report,
    WorldStateSnapshot,
)


class SchemaArtifact(ContractBaseModel):
    """单个 JSON Schema 导出产物的清单记录。"""

    name: str
    source_model: str
    artifact_type: Literal["json_schema"] = "json_schema"
    version: VersionString = __version__
    output_path: str


SCHEMA_MODEL_REGISTRY: Mapping[str, type[ContractBaseModel]] = MappingProxyType(
    {
        "base_ex_payload": BaseExPayload,
        "ex0_metadata": Ex0Metadata,
        "ex1_candidate_fact": Ex1CandidateFact,
        "ex2_candidate_signal": Ex2CandidateSignal,
        "ex3_candidate_graph_delta": Ex3CandidateGraphDelta,
        "alpha_result": AlphaResult,
        "cycle_metadata": CycleMetadata,
        "formal_object_base": FormalObjectBase,
        "world_state_snapshot": WorldStateSnapshot,
        "official_alpha_pool": OfficialAlphaPool,
        "alpha_result_snapshot": AlphaResultSnapshot,
        "recommendation_snapshot": RecommendationSnapshot,
        "dashboard_snapshot": DashboardSnapshot,
        "report": Report,
        "audit_record": AuditRecord,
        "replay_record": ReplayRecord,
    }
)


def iter_schema_models() -> Iterator[tuple[str, type[ContractBaseModel]]]:
    """按稳定 registry 顺序返回待导出的 Pydantic 模型。"""

    yield from SCHEMA_MODEL_REGISTRY.items()


def export_json_schemas(
    output_dir: str | Path,
    *,
    version: str = __version__,
) -> tuple[SchemaArtifact, ...]:
    """把 registry 中的 Pydantic 模型导出为 JSON Schema 文件。"""

    schema_dir = Path(output_dir)
    schema_dir.mkdir(parents=True, exist_ok=True)

    artifacts: list[SchemaArtifact] = []
    for name, model in iter_schema_models():
        source_model = f"{model.__module__}.{model.__qualname__}"
        schema = model.model_json_schema()
        schema["x-contract-version"] = version
        schema["x-source-model"] = source_model

        schema_path = schema_dir / f"{name}.schema.json"
        schema_path.write_text(
            json.dumps(schema, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        artifacts.append(
            SchemaArtifact(
                name=name,
                source_model=source_model,
                version=version,
                output_path=str(schema_path),
            )
        )

    manifest = {
        "artifact_type": "json_schema",
        "version": version,
        "artifacts": [artifact.model_dump() for artifact in artifacts],
    }
    (schema_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return tuple(artifacts)


__all__ = [
    "SchemaArtifact",
    "SCHEMA_MODEL_REGISTRY",
    "iter_schema_models",
    "export_json_schemas",
]
