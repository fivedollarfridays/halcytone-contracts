"""Tests for halcytone_contracts.baseline."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from halcytone_contracts.baseline import Baseline, StreamBaseline
from halcytone_contracts.signals import RESERVED_STREAMS


def _sample_stream_baseline_kwargs() -> dict:
    return {"mean": 0.5, "stddev": 0.1, "sample_count": 6000}


def _sample_baseline_kwargs() -> dict:
    return {
        "streams": {
            "breath.rate": StreamBaseline(mean=6.2, stddev=0.4, sample_count=600),
            "hrv.rmssd": StreamBaseline(mean=48.3, stddev=5.1, sample_count=60),
            "eeg.alpha": StreamBaseline(mean=0.42, stddev=0.08, sample_count=600),
        },
        "duration_s": 60,
        "captured_at": datetime(2026, 4, 17, 14, 30, 22, tzinfo=UTC),
    }


# ---------------------------------------------------------------------------
# StreamBaseline
# ---------------------------------------------------------------------------


def test_stream_baseline_constructs_from_sample() -> None:
    sb = StreamBaseline(**_sample_stream_baseline_kwargs())
    assert sb.mean == 0.5
    assert sb.stddev == 0.1
    assert sb.sample_count == 6000


def test_stream_baseline_field_set() -> None:
    assert set(StreamBaseline.model_fields.keys()) == {"mean", "stddev", "sample_count"}


def test_stream_baseline_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        StreamBaseline(mean=0.5, stddev=0.1, sample_count=10, extra_field="nope")


def test_stream_baseline_rejects_negative_stddev() -> None:
    with pytest.raises(ValidationError):
        StreamBaseline(mean=0.5, stddev=-0.01, sample_count=10)


def test_stream_baseline_accepts_zero_stddev() -> None:
    """Zero stddev is valid for constant-signal baselines."""
    sb = StreamBaseline(mean=0.5, stddev=0.0, sample_count=10)
    assert sb.stddev == 0.0


def test_stream_baseline_rejects_sample_count_zero() -> None:
    with pytest.raises(ValidationError):
        StreamBaseline(mean=0.5, stddev=0.1, sample_count=0)


def test_stream_baseline_rejects_negative_sample_count() -> None:
    with pytest.raises(ValidationError):
        StreamBaseline(mean=0.5, stddev=0.1, sample_count=-1)


def test_stream_baseline_accepts_sample_count_one() -> None:
    sb = StreamBaseline(mean=0.5, stddev=0.0, sample_count=1)
    assert sb.sample_count == 1


def test_stream_baseline_mean_allows_negative() -> None:
    """Mean can be any real number (e.g., eda_phasic centered values)."""
    sb = StreamBaseline(mean=-0.35, stddev=0.1, sample_count=10)
    assert sb.mean == -0.35


def test_stream_baseline_json_round_trip() -> None:
    sb = StreamBaseline(**_sample_stream_baseline_kwargs())
    assert StreamBaseline.model_validate_json(sb.model_dump_json()) == sb


# ---------------------------------------------------------------------------
# Baseline — basic shape
# ---------------------------------------------------------------------------


def test_baseline_constructs_from_sample() -> None:
    b = Baseline(**_sample_baseline_kwargs())
    assert b.duration_s == 60
    assert set(b.streams.keys()) == {"breath.rate", "hrv.rmssd", "eeg.alpha"}


def test_baseline_field_set() -> None:
    assert set(Baseline.model_fields.keys()) == {"streams", "duration_s", "captured_at"}


def test_baseline_forbids_extra_fields() -> None:
    kwargs = _sample_baseline_kwargs()
    kwargs["rogue"] = "nope"
    with pytest.raises(ValidationError):
        Baseline(**kwargs)


def test_baseline_rejects_duration_zero() -> None:
    kwargs = _sample_baseline_kwargs()
    kwargs["duration_s"] = 0
    with pytest.raises(ValidationError):
        Baseline(**kwargs)


def test_baseline_rejects_negative_duration() -> None:
    kwargs = _sample_baseline_kwargs()
    kwargs["duration_s"] = -1
    with pytest.raises(ValidationError):
        Baseline(**kwargs)


def test_baseline_accepts_duration_one() -> None:
    kwargs = _sample_baseline_kwargs()
    kwargs["duration_s"] = 1
    b = Baseline(**kwargs)
    assert b.duration_s == 1


# ---------------------------------------------------------------------------
# Baseline — stream-key validation against RESERVED_STREAMS
# ---------------------------------------------------------------------------


def test_baseline_rejects_empty_streams_dict() -> None:
    kwargs = _sample_baseline_kwargs()
    kwargs["streams"] = {}
    with pytest.raises(ValidationError):
        Baseline(**kwargs)


def test_baseline_rejects_unknown_stream_name() -> None:
    kwargs = _sample_baseline_kwargs()
    kwargs["streams"] = {
        "not.a.real.stream": StreamBaseline(mean=0.0, stddev=0.0, sample_count=1)
    }
    with pytest.raises(ValidationError) as excinfo:
        Baseline(**kwargs)
    assert "not.a.real.stream" in str(excinfo.value)


def test_baseline_error_message_names_all_unknown_streams() -> None:
    kwargs = _sample_baseline_kwargs()
    kwargs["streams"] = {
        "breath.rate": StreamBaseline(mean=6.0, stddev=0.1, sample_count=10),
        "bogus.one": StreamBaseline(mean=0.0, stddev=0.0, sample_count=1),
        "bogus.two": StreamBaseline(mean=0.0, stddev=0.0, sample_count=1),
    }
    with pytest.raises(ValidationError) as excinfo:
        Baseline(**kwargs)
    msg = str(excinfo.value)
    assert "bogus.one" in msg
    assert "bogus.two" in msg


def test_baseline_accepts_every_reserved_stream_name() -> None:
    """Every name in RESERVED_STREAMS must be a valid baseline key."""
    kwargs = _sample_baseline_kwargs()
    kwargs["streams"] = {
        name: StreamBaseline(mean=0.0, stddev=0.0, sample_count=1)
        for name in RESERVED_STREAMS
    }
    b = Baseline(**kwargs)
    assert set(b.streams.keys()) == set(RESERVED_STREAMS.keys())


def test_baseline_accepts_single_reserved_stream() -> None:
    kwargs = _sample_baseline_kwargs()
    kwargs["streams"] = {
        "breath.rate": StreamBaseline(mean=6.2, stddev=0.4, sample_count=600)
    }
    b = Baseline(**kwargs)
    assert list(b.streams.keys()) == ["breath.rate"]


# ---------------------------------------------------------------------------
# Baseline — JSON round-trip
# ---------------------------------------------------------------------------


def test_baseline_json_round_trip() -> None:
    populated = Baseline(**_sample_baseline_kwargs())
    round_tripped = Baseline.model_validate_json(populated.model_dump_json())
    assert round_tripped == populated


def test_baseline_json_round_trip_via_dict() -> None:
    populated = Baseline(**_sample_baseline_kwargs())
    round_tripped = Baseline.model_validate(populated.model_dump(mode="json"))
    assert round_tripped == populated


def test_baseline_json_round_trip_rejects_unknown_stream_at_parse_time() -> None:
    """Unknown streams fail parse-time validation, not only constructor-time."""
    populated = Baseline(**_sample_baseline_kwargs())
    payload = populated.model_dump(mode="json")
    payload["streams"]["not.a.real.stream"] = {"mean": 0.0, "stddev": 0.0, "sample_count": 1}
    with pytest.raises(ValidationError) as excinfo:
        Baseline.model_validate(payload)
    assert "not.a.real.stream" in str(excinfo.value)
