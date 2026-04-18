"""Tests for halcytone_contracts.summary."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from halcytone_contracts.summary import SessionSummary


def _sample_summary_kwargs() -> dict:
    return {
        "summary_schema_version": 1,
        "mean_hr": 64.2,
        "mean_hrv_rmssd": 48.1,
        "mean_breath_rate": 6.3,
        "mean_breath_depth": 0.62,
        "mean_eeg_alpha": 0.41,
        "mean_eeg_theta": 0.27,
        "mean_overall_presence": 0.55,
        "peak_heart_breath_coherence": 0.83,
        "total_annotations": 7,
    }


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


def test_session_summary_constructs_from_sample() -> None:
    s = SessionSummary(**_sample_summary_kwargs())
    assert s.summary_schema_version == 1
    assert s.mean_hr == 64.2
    assert s.total_annotations == 7


def test_session_summary_field_set() -> None:
    assert set(SessionSummary.model_fields.keys()) == {
        "summary_schema_version",
        "mean_hr",
        "mean_hrv_rmssd",
        "mean_breath_rate",
        "mean_breath_depth",
        "mean_eeg_alpha",
        "mean_eeg_theta",
        "mean_overall_presence",
        "peak_heart_breath_coherence",
        "total_annotations",
    }


def test_session_summary_schema_version_is_first_field() -> None:
    """summary_schema_version must lead the field declaration order."""
    assert next(iter(SessionSummary.model_fields.keys())) == "summary_schema_version"


def test_session_summary_schema_version_default_is_one() -> None:
    kwargs = _sample_summary_kwargs()
    kwargs.pop("summary_schema_version")
    s = SessionSummary(**kwargs)
    assert s.summary_schema_version == 1


def test_session_summary_forbids_extra_fields() -> None:
    kwargs = _sample_summary_kwargs()
    kwargs["rogue"] = "nope"
    with pytest.raises(ValidationError):
        SessionSummary(**kwargs)


# ---------------------------------------------------------------------------
# Schema-version bound
# ---------------------------------------------------------------------------


def test_session_summary_rejects_schema_version_zero() -> None:
    kwargs = _sample_summary_kwargs()
    kwargs["summary_schema_version"] = 0
    with pytest.raises(ValidationError):
        SessionSummary(**kwargs)


def test_session_summary_rejects_negative_schema_version() -> None:
    kwargs = _sample_summary_kwargs()
    kwargs["summary_schema_version"] = -1
    with pytest.raises(ValidationError):
        SessionSummary(**kwargs)


def test_session_summary_accepts_higher_schema_version() -> None:
    """Future schema versions must parse; consumers gate behavior on the int."""
    kwargs = _sample_summary_kwargs()
    kwargs["summary_schema_version"] = 7
    s = SessionSummary(**kwargs)
    assert s.summary_schema_version == 7


# ---------------------------------------------------------------------------
# Bounded-field rejection (parametrized across every [0,1] field)
# ---------------------------------------------------------------------------


_BOUNDED_FIELDS = [
    "mean_breath_depth",
    "mean_eeg_alpha",
    "mean_eeg_theta",
    "mean_overall_presence",
    "peak_heart_breath_coherence",
]


@pytest.mark.parametrize("field", _BOUNDED_FIELDS)
def test_session_summary_rejects_below_zero(field: str) -> None:
    kwargs = _sample_summary_kwargs()
    kwargs[field] = -0.01
    with pytest.raises(ValidationError):
        SessionSummary(**kwargs)


@pytest.mark.parametrize("field", _BOUNDED_FIELDS)
def test_session_summary_rejects_above_one(field: str) -> None:
    kwargs = _sample_summary_kwargs()
    kwargs[field] = 1.01
    with pytest.raises(ValidationError):
        SessionSummary(**kwargs)


@pytest.mark.parametrize("field", _BOUNDED_FIELDS)
def test_session_summary_accepts_zero_edge(field: str) -> None:
    kwargs = _sample_summary_kwargs()
    kwargs[field] = 0.0
    s = SessionSummary(**kwargs)
    assert getattr(s, field) == 0.0


@pytest.mark.parametrize("field", _BOUNDED_FIELDS)
def test_session_summary_accepts_one_edge(field: str) -> None:
    kwargs = _sample_summary_kwargs()
    kwargs[field] = 1.0
    s = SessionSummary(**kwargs)
    assert getattr(s, field) == 1.0


# ---------------------------------------------------------------------------
# total_annotations bound
# ---------------------------------------------------------------------------


def test_session_summary_rejects_negative_total_annotations() -> None:
    kwargs = _sample_summary_kwargs()
    kwargs["total_annotations"] = -1
    with pytest.raises(ValidationError):
        SessionSummary(**kwargs)


def test_session_summary_accepts_zero_total_annotations() -> None:
    kwargs = _sample_summary_kwargs()
    kwargs["total_annotations"] = 0
    s = SessionSummary(**kwargs)
    assert s.total_annotations == 0


# ---------------------------------------------------------------------------
# Unbounded numeric fields stay unbounded
# ---------------------------------------------------------------------------


def test_session_summary_mean_hr_unbounded_above() -> None:
    """No upper bound on heart-rate aggregate (consumers rule on plausibility)."""
    kwargs = _sample_summary_kwargs()
    kwargs["mean_hr"] = 240.0
    s = SessionSummary(**kwargs)
    assert s.mean_hr == 240.0


def test_session_summary_mean_breath_rate_unbounded() -> None:
    kwargs = _sample_summary_kwargs()
    kwargs["mean_breath_rate"] = 30.0
    s = SessionSummary(**kwargs)
    assert s.mean_breath_rate == 30.0


# ---------------------------------------------------------------------------
# JSON round-trip
# ---------------------------------------------------------------------------


def test_session_summary_json_round_trip() -> None:
    populated = SessionSummary(**_sample_summary_kwargs())
    round_tripped = SessionSummary.model_validate_json(populated.model_dump_json())
    assert round_tripped == populated


def test_session_summary_json_round_trip_via_dict() -> None:
    populated = SessionSummary(**_sample_summary_kwargs())
    round_tripped = SessionSummary.model_validate(populated.model_dump(mode="json"))
    assert round_tripped == populated
