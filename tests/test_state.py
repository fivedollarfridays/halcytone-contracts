"""Tests for halcytone_contracts.state."""

from __future__ import annotations

import json

import pytest
from pydantic import BaseModel, ValidationError

from halcytone_contracts.state import StateVector


def _sample_state_kwargs() -> dict:
    return {
        "t_ns": 1_700_000_000_000_000_000,
        "session_id": "20260417-143022-k7m2",
        # breath
        "breath_phase": 0.25,
        "breath_rate": 6.2,
        "breath_depth": 0.7,
        "breath_quality": 0.95,
        # cardiovascular
        "heart_rate": 62.1,
        "hrv_rmssd": 48.3,
        "hrv_quality": 0.9,
        # autonomic
        "eda_level": 3.4,
        "eda_phasic": 0.12,
        # neural
        "eeg_alpha": 0.42,
        "eeg_theta": 0.18,
        "eeg_beta": 0.3,
        "eeg_delta": 0.05,
        "eeg_gamma": 0.05,
        "eeg_quality": 0.88,
        # composite
        "heart_breath_coherence": 0.55,
        "overall_presence": 0.7,
    }


# ---------------------------------------------------------------------------
# Field set / shape
# ---------------------------------------------------------------------------


def test_state_vector_has_all_readme_fields() -> None:
    expected = {
        "t_ns",
        "session_id",
        "breath_phase",
        "breath_rate",
        "breath_depth",
        "breath_quality",
        "heart_rate",
        "hrv_rmssd",
        "hrv_quality",
        "eda_level",
        "eda_phasic",
        "eeg_alpha",
        "eeg_theta",
        "eeg_beta",
        "eeg_delta",
        "eeg_gamma",
        "eeg_quality",
        "heart_breath_coherence",
        "overall_presence",
    }
    assert set(StateVector.model_fields.keys()) == expected


def test_state_vector_constructs_from_sample() -> None:
    sv = StateVector(**_sample_state_kwargs())
    for key, value in _sample_state_kwargs().items():
        assert getattr(sv, key) == value


def test_state_vector_is_flat_struct_no_nested_submodels() -> None:
    """Flat struct by choice — no StateVector field is itself a pydantic model."""
    for field_name, field_info in StateVector.model_fields.items():
        annotation = field_info.annotation
        assert not (
            isinstance(annotation, type) and issubclass(annotation, BaseModel)
        ), f"Field {field_name!r} is a nested pydantic model; flat struct required"


def test_state_vector_field_types() -> None:
    fields = StateVector.model_fields
    assert fields["t_ns"].annotation is int
    assert fields["session_id"].annotation is str
    for name in (
        "breath_phase",
        "breath_rate",
        "breath_depth",
        "breath_quality",
        "heart_rate",
        "hrv_rmssd",
        "hrv_quality",
        "eda_level",
        "eda_phasic",
        "eeg_alpha",
        "eeg_theta",
        "eeg_beta",
        "eeg_delta",
        "eeg_gamma",
        "eeg_quality",
        "heart_breath_coherence",
        "overall_presence",
    ):
        assert fields[name].annotation is float, name


def test_state_vector_rejects_unknown_field() -> None:
    kwargs = _sample_state_kwargs()
    kwargs["mystery"] = 1.0
    with pytest.raises(ValidationError):
        StateVector(**kwargs)


@pytest.mark.parametrize(
    "bad_id",
    [
        "",
        "not-a-session-id",
        "20260417-143022",
        "20260417-143022-toolongslug",
        "20260417-143022-A7M2",  # uppercase — alphabet is [0-9a-z]
    ],
)
def test_state_vector_rejects_invalid_session_id(bad_id: str) -> None:
    """session_id must match the canonical regex, same as SessionStart/SessionManifest."""
    kwargs = _sample_state_kwargs()
    kwargs["session_id"] = bad_id
    with pytest.raises(ValidationError):
        StateVector(**kwargs)


# ---------------------------------------------------------------------------
# Range-validated fields (AC: explicit [0, 1] normalization)
# ---------------------------------------------------------------------------


BOUNDED_ZERO_ONE_FIELDS = [
    "breath_phase",
    "breath_depth",
    "breath_quality",
    "hrv_quality",
    "eeg_alpha",
    "eeg_theta",
    "eeg_beta",
    "eeg_delta",
    "eeg_gamma",
    "eeg_quality",
    "heart_breath_coherence",
    "overall_presence",
]


@pytest.mark.parametrize("field", BOUNDED_ZERO_ONE_FIELDS)
@pytest.mark.parametrize("bad_value", [-0.01, 1.01, -1.0, 2.0])
def test_bounded_fields_reject_out_of_range(field: str, bad_value: float) -> None:
    kwargs = _sample_state_kwargs()
    kwargs[field] = bad_value
    with pytest.raises(ValidationError):
        StateVector(**kwargs)


@pytest.mark.parametrize("field", BOUNDED_ZERO_ONE_FIELDS)
@pytest.mark.parametrize("edge", [0.0, 1.0])
def test_bounded_fields_accept_inclusive_edges(field: str, edge: float) -> None:
    kwargs = _sample_state_kwargs()
    kwargs[field] = edge
    sv = StateVector(**kwargs)
    assert getattr(sv, field) == edge


# ---------------------------------------------------------------------------
# Round-trip serialization
# ---------------------------------------------------------------------------


def test_state_vector_json_round_trip_preserves_all_fields() -> None:
    sv = StateVector(**_sample_state_kwargs())
    payload = sv.model_dump_json()
    parsed = StateVector.model_validate_json(payload)
    assert parsed == sv
    assert parsed.model_dump() == sv.model_dump()


def test_state_vector_dict_round_trip() -> None:
    sv = StateVector(**_sample_state_kwargs())
    parsed = StateVector.model_validate(sv.model_dump())
    assert parsed == sv


# ---------------------------------------------------------------------------
# JSONL-line serialization (state.jsonl, per README)
# ---------------------------------------------------------------------------


def test_state_vector_jsonl_line_fits_one_line() -> None:
    sv = StateVector(**_sample_state_kwargs())
    line = sv.model_dump_json()
    assert "\n" not in line
    assert "\r" not in line


def test_state_vector_jsonl_line_parses_back() -> None:
    sv = StateVector(**_sample_state_kwargs())
    line = sv.model_dump_json()
    parsed = StateVector.model_validate_json(line)
    assert parsed == sv


def test_state_vector_jsonl_line_is_valid_json() -> None:
    sv = StateVector(**_sample_state_kwargs())
    line = sv.model_dump_json()
    # standard json lib can parse it too — it's ordinary JSON
    doc = json.loads(line)
    assert doc["session_id"] == "20260417-143022-k7m2"
    assert doc["t_ns"] == 1_700_000_000_000_000_000


def test_state_vector_multiple_records_as_jsonl() -> None:
    """Simulate state.jsonl: write N records, read N records, each one line."""
    records = [StateVector(**_sample_state_kwargs()) for _ in range(3)]
    blob = "\n".join(r.model_dump_json() for r in records)
    lines = blob.split("\n")
    assert len(lines) == 3
    roundtrip = [StateVector.model_validate_json(line) for line in lines]
    assert roundtrip == records
