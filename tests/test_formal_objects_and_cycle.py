from __future__ import annotations

import pathlib
import sys
from datetime import datetime, timedelta, timezone

import pydantic
import pytest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_DIR))
try:
    from contracts.core import Zone
    from contracts.errors import ContractError, ErrorCode
    from contracts.schemas import (
        FORMAL_OBJECT_REGISTRY,
        AlphaResultSnapshot,
        AuditRecord,
        CycleMetadata,
        CyclePhase,
        DashboardSnapshot,
        FormalObjectBase,
        FormalObjectName,
        OfficialAlphaPool,
        RecommendationSnapshot,
        ReplayRecord,
        Report,
        WorldStateSnapshot,
        get_formal_object_model,
    )
finally:
    sys.path.remove(str(SRC_DIR))


def valid_formal_object_payload(name: FormalObjectName) -> dict[str, object]:
    return {
        "object_id": f"{name.value}-001",
        "version": "0.1.0",
        "created_at": datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc),
        "payload": {"object_name": name.value},
    }


def valid_cycle_payload() -> dict[str, object]:
    return {
        "cycle_id": "cycle-20260415-001",
        "phase": "collecting",
        "started_at": datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc),
    }


def test_formal_object_registry_is_exact() -> None:
    expected_models = {
        FormalObjectName.WORLD_STATE_SNAPSHOT: WorldStateSnapshot,
        FormalObjectName.OFFICIAL_ALPHA_POOL: OfficialAlphaPool,
        FormalObjectName.ALPHA_RESULT_SNAPSHOT: AlphaResultSnapshot,
        FormalObjectName.RECOMMENDATION_SNAPSHOT: RecommendationSnapshot,
        FormalObjectName.DASHBOARD_SNAPSHOT: DashboardSnapshot,
        FormalObjectName.REPORT: Report,
        FormalObjectName.AUDIT_RECORD: AuditRecord,
        FormalObjectName.REPLAY_RECORD: ReplayRecord,
    }

    assert set(FORMAL_OBJECT_REGISTRY) == set(FormalObjectName)
    assert dict(FORMAL_OBJECT_REGISTRY) == expected_models
    assert len(FORMAL_OBJECT_REGISTRY) == 8


def test_backtest_result_is_not_a_formal_object() -> None:
    assert "backtest_result" not in {name.value for name in FormalObjectName}
    assert "backtest_result" not in {
        name.value for name in FORMAL_OBJECT_REGISTRY
    }

    with pytest.raises(ValueError):
        FormalObjectName("backtest_result")

    with pytest.raises(ContractError) as exc_info:
        get_formal_object_model("backtest_result")

    assert exc_info.value.code is ErrorCode.UNKNOWN_FORMAL_OBJECT
    assert exc_info.value.details == {"object_name": "backtest_result"}


def test_each_formal_object_model_validates_minimal_payload() -> None:
    for object_name, model in FORMAL_OBJECT_REGISTRY.items():
        instance = model.model_validate(valid_formal_object_payload(object_name))

        assert isinstance(instance, FormalObjectBase)
        assert instance.object_name is object_name
        assert instance.zone is Zone.FORMAL
        assert instance.payload == {"object_name": object_name.value}
        assert get_formal_object_model(object_name) is model
        assert get_formal_object_model(object_name.value) is model

        invalid_zone_payload = {
            **valid_formal_object_payload(object_name),
            "zone": "analytical",
        }
        with pytest.raises(pydantic.ValidationError):
            model.model_validate(invalid_zone_payload)

        for required_field in ("object_id", "version", "created_at", "payload"):
            invalid_payload = valid_formal_object_payload(object_name)
            invalid_payload.pop(required_field)

            with pytest.raises(pydantic.ValidationError):
                model.model_validate(invalid_payload)


def test_cycle_metadata_time_constraints() -> None:
    started_at = datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc)

    assert {phase.value for phase in CyclePhase} == {
        "collecting",
        "analyzing",
        "publishing",
        "completed",
        "failed",
    }

    in_progress = CycleMetadata.model_validate(
        {**valid_cycle_payload(), "started_at": started_at}
    )
    assert in_progress.phase is CyclePhase.COLLECTING
    assert in_progress.ended_at is None
    assert in_progress.previous_cycle_id is None

    ended = CycleMetadata.model_validate(
        {
            **valid_cycle_payload(),
            "phase": "completed",
            "started_at": started_at,
            "ended_at": started_at + timedelta(minutes=30),
            "previous_cycle_id": "cycle-20260415-000",
        }
    )
    assert ended.phase is CyclePhase.COMPLETED
    assert ended.ended_at == started_at + timedelta(minutes=30)
    assert ended.previous_cycle_id == "cycle-20260415-000"

    same_time_ended = CycleMetadata.model_validate(
        {
            **valid_cycle_payload(),
            "phase": "completed",
            "started_at": started_at,
            "ended_at": started_at,
        }
    )
    assert same_time_ended.ended_at == started_at

    with pytest.raises(pydantic.ValidationError):
        CycleMetadata.model_validate({**valid_cycle_payload(), "phase": "paused"})

    for field_name in ("started_at", "ended_at"):
        with pytest.raises(pydantic.ValidationError, match="timezone-aware"):
            CycleMetadata.model_validate(
                {
                    **valid_cycle_payload(),
                    field_name: datetime(2026, 4, 15, 12, 0),
                }
            )

    with pytest.raises(pydantic.ValidationError, match="ended_at"):
        CycleMetadata.model_validate(
            {
                **valid_cycle_payload(),
                "started_at": started_at,
                "ended_at": started_at - timedelta(seconds=1),
            }
        )

    for previous_cycle_id in ("", "   "):
        with pytest.raises(pydantic.ValidationError):
            CycleMetadata.model_validate(
                {
                    **valid_cycle_payload(),
                    "previous_cycle_id": previous_cycle_id,
                }
            )


def test_formal_and_cycle_json_schema_generation() -> None:
    for model in FORMAL_OBJECT_REGISTRY.values():
        schema = model.model_json_schema()

        assert schema["type"] == "object"
        assert "properties" in schema

    cycle_schema = CycleMetadata.model_json_schema()

    assert cycle_schema["type"] == "object"
    assert set(cycle_schema["required"]).issuperset(
        {"cycle_id", "phase", "started_at"}
    )
