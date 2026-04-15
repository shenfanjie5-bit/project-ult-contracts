from __future__ import annotations

import importlib
import pathlib
import sys
from datetime import datetime, timedelta, timezone

import pydantic
import pytest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"


def import_cycle_schema() -> tuple[type, type]:
    sys.path.insert(0, str(SRC_DIR))
    try:
        schemas = importlib.import_module("contracts.schemas")
    finally:
        sys.path.remove(str(SRC_DIR))

    return schemas.CycleMetadata, schemas.CyclePhase


def valid_cycle_payload() -> dict[str, object]:
    return {
        "cycle_id": "cycle-20260415-001",
        "phase": "collecting",
        "started_at": datetime(2026, 4, 15, 9, 0, tzinfo=timezone.utc),
    }


def test_cycle_metadata_is_reexported_from_schemas() -> None:
    CycleMetadata, CyclePhase = import_cycle_schema()

    assert CycleMetadata.__name__ == "CycleMetadata"
    assert CyclePhase.COLLECTING.value == "collecting"
    assert "CycleMetadata" in importlib.import_module("contracts.schemas").__all__
    assert "CyclePhase" in importlib.import_module("contracts.schemas").__all__


def test_ongoing_cycle_with_no_end_time_is_valid() -> None:
    CycleMetadata, CyclePhase = import_cycle_schema()

    cycle = CycleMetadata.model_validate(valid_cycle_payload())

    assert cycle.cycle_id == "cycle-20260415-001"
    assert cycle.phase is CyclePhase.COLLECTING
    assert cycle.ended_at is None
    assert cycle.previous_cycle_id is None
    assert cycle.version == "0.1.0"


def test_completed_cycle_with_end_time_after_start_is_valid() -> None:
    CycleMetadata, CyclePhase = import_cycle_schema()
    started_at = datetime(2026, 4, 15, 9, 0, tzinfo=timezone.utc)

    cycle = CycleMetadata.model_validate(
        {
            **valid_cycle_payload(),
            "phase": "completed",
            "started_at": started_at,
            "ended_at": started_at + timedelta(minutes=30),
            "previous_cycle_id": "cycle-20260415-000",
        },
    )

    assert cycle.phase is CyclePhase.COMPLETED
    assert cycle.ended_at == started_at + timedelta(minutes=30)
    assert cycle.previous_cycle_id == "cycle-20260415-000"


def test_cycle_metadata_json_schema_marks_minimum_required_fields() -> None:
    CycleMetadata, _ = import_cycle_schema()

    required_fields = set(CycleMetadata.model_json_schema()["required"])

    assert {"cycle_id", "phase", "started_at"}.issubset(required_fields)
    assert "ended_at" not in required_fields
    assert "previous_cycle_id" not in required_fields
    assert "version" not in required_fields


def test_ended_at_before_started_at_is_rejected() -> None:
    CycleMetadata, _ = import_cycle_schema()
    started_at = datetime(2026, 4, 15, 9, 0, tzinfo=timezone.utc)

    with pytest.raises(pydantic.ValidationError):
        CycleMetadata.model_validate(
            {
                **valid_cycle_payload(),
                "started_at": started_at,
                "ended_at": started_at - timedelta(seconds=1),
            },
        )


@pytest.mark.parametrize(
    ("field_name", "invalid_value"),
    [
        (
            "started_at",
            datetime(2026, 4, 15, 10, 0, tzinfo=timezone.utc),
        ),
        (
            "ended_at",
            datetime(2026, 4, 15, 8, 59, 59, tzinfo=timezone.utc),
        ),
    ],
)
def test_failed_cycle_time_assignment_leaves_original_values_unchanged(
    field_name: str,
    invalid_value: datetime,
) -> None:
    CycleMetadata, _ = import_cycle_schema()
    started_at = datetime(2026, 4, 15, 9, 0, tzinfo=timezone.utc)
    ended_at = started_at + timedelta(minutes=30)
    cycle = CycleMetadata.model_validate(
        {
            **valid_cycle_payload(),
            "phase": "completed",
            "started_at": started_at,
            "ended_at": ended_at,
        },
    )

    with pytest.raises(pydantic.ValidationError):
        setattr(cycle, field_name, invalid_value)

    assert cycle.started_at == started_at
    assert cycle.ended_at == ended_at


@pytest.mark.parametrize(
    "field_name",
    [
        "started_at",
        "ended_at",
    ],
)
def test_cycle_datetime_fields_must_be_timezone_aware(field_name: str) -> None:
    CycleMetadata, _ = import_cycle_schema()

    with pytest.raises(pydantic.ValidationError):
        CycleMetadata.model_validate(
            {
                **valid_cycle_payload(),
                field_name: datetime(2026, 4, 15, 9, 0),
            },
        )


def test_unknown_cycle_phase_is_rejected() -> None:
    CycleMetadata, _ = import_cycle_schema()

    with pytest.raises(pydantic.ValidationError):
        CycleMetadata.model_validate({**valid_cycle_payload(), "phase": "queued"})


def test_previous_cycle_id_accepts_none_or_non_empty_string() -> None:
    CycleMetadata, _ = import_cycle_schema()

    assert CycleMetadata.model_validate(
        {**valid_cycle_payload(), "previous_cycle_id": None},
    ).previous_cycle_id is None
    assert (
        CycleMetadata.model_validate(
            {**valid_cycle_payload(), "previous_cycle_id": "cycle-20260415-000"},
        ).previous_cycle_id
        == "cycle-20260415-000"
    )

    with pytest.raises(pydantic.ValidationError):
        CycleMetadata.model_validate({**valid_cycle_payload(), "previous_cycle_id": ""})
