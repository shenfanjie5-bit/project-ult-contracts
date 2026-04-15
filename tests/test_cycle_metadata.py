from __future__ import annotations

import importlib
import pathlib
import sys
from datetime import datetime, timedelta, timezone

import pydantic
import pytest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"


def import_schemas() -> object:
    sys.path.insert(0, str(SRC_DIR))
    try:
        return importlib.import_module("contracts.schemas")
    finally:
        sys.path.remove(str(SRC_DIR))


def started_at() -> datetime:
    return datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc)


def test_cycle_metadata_public_api_imports() -> None:
    schemas = import_schemas()

    assert hasattr(schemas, "CyclePhase")
    assert hasattr(schemas, "CycleMetadata")
    assert "CyclePhase" in schemas.__all__
    assert "CycleMetadata" in schemas.__all__


def test_cycle_phase_values_are_the_frozen_set() -> None:
    schemas = import_schemas()

    assert {phase.value for phase in schemas.CyclePhase} == {
        "collecting",
        "analyzing",
        "publishing",
        "completed",
        "failed",
    }


def test_in_progress_cycle_validates_with_no_ended_at() -> None:
    schemas = import_schemas()

    cycle = schemas.CycleMetadata.model_validate(
        {
            "cycle_id": "cycle-20260415-001",
            "phase": "collecting",
            "started_at": started_at(),
        }
    )

    assert cycle.phase is schemas.CyclePhase.COLLECTING
    assert cycle.ended_at is None
    assert cycle.previous_cycle_id is None
    assert cycle.version == "0.1.0"


def test_completed_cycle_validates_when_ended_at_is_after_started_at() -> None:
    schemas = import_schemas()
    start_time = started_at()

    cycle = schemas.CycleMetadata.model_validate(
        {
            "cycle_id": "cycle-20260415-002",
            "phase": "completed",
            "started_at": start_time,
            "ended_at": start_time + timedelta(minutes=30),
            "previous_cycle_id": "cycle-20260415-001",
        }
    )

    assert cycle.phase is schemas.CyclePhase.COMPLETED
    assert cycle.ended_at == start_time + timedelta(minutes=30)
    assert cycle.previous_cycle_id == "cycle-20260415-001"


def test_ended_at_can_equal_started_at() -> None:
    schemas = import_schemas()
    start_time = started_at()

    cycle = schemas.CycleMetadata.model_validate(
        {
            "cycle_id": "cycle-20260415-003",
            "phase": "failed",
            "started_at": start_time,
            "ended_at": start_time,
        }
    )

    assert cycle.ended_at == start_time


def test_ended_at_before_started_at_is_rejected() -> None:
    schemas = import_schemas()
    start_time = started_at()

    with pytest.raises(pydantic.ValidationError):
        schemas.CycleMetadata.model_validate(
            {
                "cycle_id": "cycle-20260415-004",
                "phase": "completed",
                "started_at": start_time,
                "ended_at": start_time - timedelta(seconds=1),
            }
        )


def test_rejected_time_assignment_preserves_existing_cycle_state() -> None:
    schemas = import_schemas()
    start_time = started_at()
    end_time = start_time + timedelta(minutes=30)
    cycle = schemas.CycleMetadata.model_validate(
        {
            "cycle_id": "cycle-20260415-004",
            "phase": "completed",
            "started_at": start_time,
            "ended_at": end_time,
        }
    )

    with pytest.raises(pydantic.ValidationError):
        cycle.started_at = end_time + timedelta(seconds=1)

    assert cycle.started_at == start_time
    assert cycle.ended_at == end_time

    with pytest.raises(pydantic.ValidationError):
        cycle.ended_at = start_time - timedelta(seconds=1)

    assert cycle.started_at == start_time
    assert cycle.ended_at == end_time


@pytest.mark.parametrize(
    "field_name",
    ["started_at", "ended_at"],
)
def test_cycle_timestamps_must_be_timezone_aware(field_name: str) -> None:
    schemas = import_schemas()
    payload = {
        "cycle_id": "cycle-20260415-005",
        "phase": "collecting",
        "started_at": started_at(),
        "ended_at": started_at() + timedelta(minutes=5),
    }
    payload[field_name] = datetime(2026, 4, 15, 12, 0)

    with pytest.raises(pydantic.ValidationError):
        schemas.CycleMetadata.model_validate(payload)


def test_unknown_cycle_phase_is_rejected() -> None:
    schemas = import_schemas()

    with pytest.raises(pydantic.ValidationError):
        schemas.CycleMetadata.model_validate(
            {
                "cycle_id": "cycle-20260415-006",
                "phase": "retrying",
                "started_at": started_at(),
            }
        )


def test_previous_cycle_id_rejects_empty_string() -> None:
    schemas = import_schemas()

    with pytest.raises(pydantic.ValidationError):
        schemas.CycleMetadata.model_validate(
            {
                "cycle_id": "cycle-20260415-007",
                "phase": "collecting",
                "started_at": started_at(),
                "previous_cycle_id": "",
            }
        )


def test_cycle_metadata_json_schema_required_fields() -> None:
    schemas = import_schemas()

    required_fields = set(schemas.CycleMetadata.model_json_schema()["required"])

    assert {"cycle_id", "phase", "started_at"}.issubset(required_fields)
