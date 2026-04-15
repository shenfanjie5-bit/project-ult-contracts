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


EX_PAYLOAD_HELPERS: dict[
    type[pydantic.BaseModel], Callable[[], dict[str, object]]
] = {
    Ex0Metadata: valid_ex0_payload,
    Ex1CandidateFact: valid_ex1_payload,
    Ex2CandidateSignal: valid_ex2_payload,
    Ex3CandidateGraphDelta: valid_ex3_payload,
}


def required_field_cases() -> list[pytest.ParameterSet]:
    return [
        pytest.param(model, field_name, id=f"{model.__name__}.{field_name}")
        for model, required_fields in EX_MODEL_REQUIRED_FIELDS.items()
        for field_name in sorted(required_fields)
    ]


def model_cases() -> list[pytest.ParameterSet]:
    return [
        pytest.param(model, id=model.__name__)
        for model in EX_MODEL_REQUIRED_FIELDS
    ]


@pytest.mark.parametrize("model", model_cases())
def test_valid_ex_payloads_validate(
    model: type[pydantic.BaseModel],
) -> None:
    payload = EX_PAYLOAD_HELPERS[model]()

    validated = model.model_validate(payload)

    assert validated.model_dump() == payload


@pytest.mark.parametrize(("model", "field_name"), required_field_cases())
def test_required_fields_are_enforced(
    model: type[pydantic.BaseModel],
    field_name: str,
) -> None:
    payload = EX_PAYLOAD_HELPERS[model]()
    payload.pop(field_name)

    with pytest.raises(pydantic.ValidationError):
        model.model_validate(payload)


@pytest.mark.parametrize("model", model_cases())
@pytest.mark.parametrize("field_name", sorted(FORBIDDEN_INGEST_METADATA_FIELDS))
def test_ingest_metadata_is_rejected_for_all_ex_payloads(
    model: type[pydantic.BaseModel],
    field_name: str,
) -> None:
    field_value: object
    if field_name == "submitted_at":
        field_value = datetime(2026, 4, 15, 12, 5, tzinfo=timezone.utc)
    else:
        field_value = 1
    payload = {**EX_PAYLOAD_HELPERS[model](), field_name: field_value}

    with pytest.raises(pydantic.ValidationError, match="ingest metadata"):
        model.model_validate(payload)

    assert field_name not in model.model_json_schema()["properties"]


@pytest.mark.parametrize("model", model_cases())
def test_extra_fields_are_rejected_for_all_ex_payloads(
    model: type[pydantic.BaseModel],
) -> None:
    payload = {**EX_PAYLOAD_HELPERS[model](), "unexpected_field": "not allowed"}

    with pytest.raises(pydantic.ValidationError):
        model.model_validate(payload)


@pytest.mark.parametrize(
    ("model", "field_name", "field_value"),
    [
        pytest.param(Ex0Metadata, "pending_count", -1, id="ex0.pending_count"),
        pytest.param(Ex0Metadata, "status", "unknown", id="ex0.status"),
        pytest.param(
            Ex0Metadata,
            "heartbeat_at",
            datetime(2026, 4, 15, 12, 0),
            id="ex0.heartbeat_at_naive",
        ),
        pytest.param(
            Ex0Metadata,
            "last_output_at",
            datetime(2026, 4, 15, 12, 0),
            id="ex0.last_output_at_naive",
        ),
        pytest.param(Ex1CandidateFact, "confidence", -0.01, id="ex1.confidence_low"),
        pytest.param(Ex1CandidateFact, "confidence", 1.01, id="ex1.confidence_high"),
        pytest.param(Ex1CandidateFact, "fact_content", {}, id="ex1.fact_content"),
        pytest.param(
            Ex1CandidateFact,
            "source_reference",
            {},
            id="ex1.source_reference",
        ),
        pytest.param(Ex2CandidateSignal, "direction", "sideways", id="ex2.direction"),
        pytest.param(Ex2CandidateSignal, "magnitude", -0.01, id="ex2.magnitude"),
        pytest.param(
            Ex2CandidateSignal,
            "affected_entities",
            [],
            id="ex2.affected_entities",
        ),
        pytest.param(
            Ex2CandidateSignal,
            "affected_sectors",
            [],
            id="ex2.affected_sectors",
        ),
        pytest.param(Ex2CandidateSignal, "evidence", [], id="ex2.evidence"),
        pytest.param(Ex3CandidateGraphDelta, "delta_type", "", id="ex3.delta_type"),
        pytest.param(
            Ex3CandidateGraphDelta,
            "relation_type",
            "",
            id="ex3.relation_type",
        ),
        pytest.param(Ex3CandidateGraphDelta, "evidence", [], id="ex3.evidence"),
    ],
)
def test_invalid_ex_field_values_are_rejected(
    model: type[pydantic.BaseModel],
    field_name: str,
    field_value: object,
) -> None:
    payload = {**EX_PAYLOAD_HELPERS[model](), field_name: field_value}

    with pytest.raises(pydantic.ValidationError):
        model.model_validate(payload)


def test_ex3_empty_properties_is_valid() -> None:
    payload = {**valid_ex3_payload(), "properties": {}}

    delta = Ex3CandidateGraphDelta.model_validate(payload)

    assert delta.properties == {}


@pytest.mark.parametrize("model", model_cases())
def test_ex_json_schema_required_fields_match_contract(
    model: type[pydantic.BaseModel],
) -> None:
    schema = model.model_json_schema()

    assert set(schema["required"]) == EX_MODEL_REQUIRED_FIELDS[model]
    assert FORBIDDEN_INGEST_METADATA_FIELDS.isdisjoint(schema["properties"])
