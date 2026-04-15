from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

import pydantic
import pytest

from contracts.schemas import (
    FORBIDDEN_INGEST_METADATA_FIELDS,
    Ex0Metadata,
    Ex1CandidateFact,
    Ex2CandidateSignal,
    Ex3CandidateGraphDelta,
)


PayloadFactory = Callable[[], dict[str, object]]


def valid_ex0_payload() -> dict[str, object]:
    return {
        "subsystem_id": "subsystem-news",
        "version": "0.1.0",
        "heartbeat_at": datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc),
        "status": "ok",
        "last_output_at": datetime(2026, 4, 15, 11, 55, tzinfo=timezone.utc),
        "pending_count": 0,
    }


def valid_ex1_payload() -> dict[str, object]:
    return {
        "fact_id": "fact-1",
        "entity_id": "AAPL",
        "fact_type": "earnings",
        "fact_content": {"headline": "sample"},
        "confidence": 0.8,
        "source_reference": {"source": "fixture"},
        "extracted_at": datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc),
        "subsystem_id": "subsystem-news",
    }


def valid_ex2_payload() -> dict[str, object]:
    return {
        "signal_id": "signal-1",
        "signal_type": "sentiment_shift",
        "direction": "bullish",
        "magnitude": 0.4,
        "affected_entities": ["AAPL"],
        "affected_sectors": ["technology"],
        "time_horizon": "short_term",
        "evidence": ["fact-1"],
        "confidence": 0.7,
        "subsystem_id": "subsystem-news",
    }


def valid_ex3_payload() -> dict[str, object]:
    return {
        "delta_id": "delta-1",
        "delta_type": "upsert_relation",
        "source_node": "AAPL",
        "target_node": "technology",
        "relation_type": "belongs_to_sector",
        "properties": {"weight": 1.0},
        "evidence": ["fact-1"],
        "subsystem_id": "subsystem-news",
    }


EX_MODEL_REQUIRED_FIELDS: dict[type[pydantic.BaseModel], set[str]] = {
    Ex0Metadata: {
        "subsystem_id",
        "version",
        "heartbeat_at",
        "status",
        "last_output_at",
        "pending_count",
    },
    Ex1CandidateFact: {
        "fact_id",
        "entity_id",
        "fact_type",
        "fact_content",
        "confidence",
        "source_reference",
        "extracted_at",
        "subsystem_id",
    },
    Ex2CandidateSignal: {
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
    Ex3CandidateGraphDelta: {
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


EX_MODEL_PAYLOADS: tuple[tuple[type[pydantic.BaseModel], PayloadFactory], ...] = (
    (Ex0Metadata, valid_ex0_payload),
    (Ex1CandidateFact, valid_ex1_payload),
    (Ex2CandidateSignal, valid_ex2_payload),
    (Ex3CandidateGraphDelta, valid_ex3_payload),
)


REQUIRED_FIELD_CASES: tuple[
    tuple[type[pydantic.BaseModel], PayloadFactory, str],
    ...,
] = (
    tuple(
        (model, payload_factory, field_name)
        for model, payload_factory in EX_MODEL_PAYLOADS
        for field_name in sorted(EX_MODEL_REQUIRED_FIELDS[model])
    )
)


@pytest.mark.parametrize(("model", "payload_factory"), EX_MODEL_PAYLOADS)
def test_valid_ex_payloads_validate(
    model: type[pydantic.BaseModel],
    payload_factory: PayloadFactory,
) -> None:
    payload = payload_factory()

    parsed = model.model_validate(payload)

    assert parsed.model_dump() == payload


@pytest.mark.parametrize(
    ("model", "payload_factory", "field_name"),
    REQUIRED_FIELD_CASES,
)
def test_required_fields_are_enforced(
    model: type[pydantic.BaseModel],
    payload_factory: PayloadFactory,
    field_name: str,
) -> None:
    payload = payload_factory()
    payload.pop(field_name)

    with pytest.raises(pydantic.ValidationError):
        model.model_validate(payload)


@pytest.mark.parametrize(("model", "payload_factory"), EX_MODEL_PAYLOADS)
def test_extra_fields_are_rejected_for_all_ex_payloads(
    model: type[pydantic.BaseModel],
    payload_factory: PayloadFactory,
) -> None:
    payload = {**payload_factory(), "unexpected_field": "not allowed"}

    with pytest.raises(pydantic.ValidationError):
        model.model_validate(payload)


@pytest.mark.parametrize(("model", "payload_factory"), EX_MODEL_PAYLOADS)
@pytest.mark.parametrize("field_name", sorted(FORBIDDEN_INGEST_METADATA_FIELDS))
def test_ingest_metadata_is_rejected_for_all_ex_payloads(
    model: type[pydantic.BaseModel],
    payload_factory: PayloadFactory,
    field_name: str,
) -> None:
    payload = {
        **payload_factory(),
        field_name: datetime(2026, 4, 15, 12, 5, tzinfo=timezone.utc),
    }

    with pytest.raises(pydantic.ValidationError, match="ingest metadata"):
        model.model_validate(payload)


@pytest.mark.parametrize(("model", "payload_factory"), EX_MODEL_PAYLOADS)
def test_ex_json_schema_required_fields_match_contract(
    model: type[pydantic.BaseModel],
    payload_factory: PayloadFactory,
) -> None:
    del payload_factory

    schema = model.model_json_schema()

    assert set(schema["required"]) == EX_MODEL_REQUIRED_FIELDS[model]
    assert FORBIDDEN_INGEST_METADATA_FIELDS.isdisjoint(schema["properties"])


@pytest.mark.parametrize(
    ("field_name", "field_value", "match"),
    [
        ("pending_count", -1, None),
        ("status", "unknown", None),
        ("heartbeat_at", datetime(2026, 4, 15, 12, 0), "timezone-aware"),
    ],
)
def test_ex0_invalid_values_are_rejected(
    field_name: str,
    field_value: object,
    match: str | None,
) -> None:
    payload = {**valid_ex0_payload(), field_name: field_value}

    with pytest.raises(pydantic.ValidationError, match=match):
        Ex0Metadata.model_validate(payload)


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("confidence", -0.01),
        ("confidence", 1.01),
        ("fact_content", {}),
        ("source_reference", {}),
    ],
)
def test_ex1_invalid_values_are_rejected(
    field_name: str,
    field_value: object,
) -> None:
    payload = {**valid_ex1_payload(), field_name: field_value}

    with pytest.raises(pydantic.ValidationError):
        Ex1CandidateFact.model_validate(payload)


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("direction", "sideways"),
        ("magnitude", -0.01),
        ("affected_entities", []),
        ("affected_sectors", []),
        ("evidence", []),
    ],
)
def test_ex2_invalid_values_are_rejected(
    field_name: str,
    field_value: object,
) -> None:
    payload = {**valid_ex2_payload(), field_name: field_value}

    with pytest.raises(pydantic.ValidationError):
        Ex2CandidateSignal.model_validate(payload)


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("delta_type", ""),
        ("relation_type", ""),
        ("evidence", []),
    ],
)
def test_ex3_invalid_values_are_rejected(
    field_name: str,
    field_value: object,
) -> None:
    payload = {**valid_ex3_payload(), field_name: field_value}

    with pytest.raises(pydantic.ValidationError):
        Ex3CandidateGraphDelta.model_validate(payload)


def test_ex3_empty_properties_is_valid() -> None:
    payload = {**valid_ex3_payload(), "properties": {}}

    delta = Ex3CandidateGraphDelta.model_validate(payload)

    assert delta.properties == {}
