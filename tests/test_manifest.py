"""Tests for halcytone_contracts.bundles.manifest."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from halcytone_contracts.bundles.manifest import SessionManifest

_EXAMPLE_ID = "20260417-143022-k7m2"
_STARTED = datetime(2026, 4, 17, 14, 30, 22, tzinfo=UTC)
_ENDED = datetime(2026, 4, 17, 15, 2, 47, tzinfo=UTC)


def _example_baseline() -> dict:
    return {
        "streams": {
            "hrv.rmssd": {"mean": 48.3, "stddev": 4.2, "sample_count": 30},
            "breath.rate": {"mean": 6.2, "stddev": 0.8, "sample_count": 60},
            "eda": {"mean": 2.1, "stddev": 0.3, "sample_count": 60},
        },
        "duration_s": 60,
        "captured_at": _STARTED,
    }


def _example_summary() -> dict:
    return {
        "summary_schema_version": 1,
        "mean_hr": 62.1,
        "mean_hrv_rmssd": 48.3,
        "mean_breath_rate": 6.2,
        "mean_breath_depth": 0.7,
        "mean_eeg_alpha": 0.35,
        "mean_eeg_theta": 0.25,
        "mean_overall_presence": 0.72,
        "peak_heart_breath_coherence": 0.68,
        "total_annotations": 3,
    }


def _example_payload(*, ended_at: datetime | None = _ENDED) -> dict:
    return {
        "session_id": _EXAMPLE_ID,
        "started_at": _STARTED,
        "ended_at": ended_at,
        "duration_s": 1945,
        "sensors": ["ganglion-01", "emotibit-01", "stemoscope-01"],
        "baselines": _example_baseline(),
        "summary": _example_summary(),
        "artifacts": {
            "video": "video.mp4",
            "audio": "audio.wav",
            "signals": "signals.xdf",
            "state": "state.jsonl",
        },
    }


# ---------------------------------------------------------------------------
# Field shape
# ---------------------------------------------------------------------------


def test_manifest_accepts_complete_payload() -> None:
    m = SessionManifest(**_example_payload())
    assert m.session_id == _EXAMPLE_ID
    assert m.started_at == _STARTED
    assert m.ended_at == _ENDED
    assert m.duration_s == 1945
    assert m.sensors == ["ganglion-01", "emotibit-01", "stemoscope-01"]
    assert m.baselines.streams["hrv.rmssd"].mean == 48.3
    assert m.baselines.streams["hrv.rmssd"].sample_count == 30
    assert m.baselines.duration_s == 60
    assert m.summary.mean_hr == 62.1
    assert m.summary.summary_schema_version == 1
    assert m.artifacts["video"] == "video.mp4"


def test_manifest_rejects_invalid_session_id() -> None:
    payload = _example_payload()
    payload["session_id"] = "not-a-valid-id"
    with pytest.raises(ValidationError):
        SessionManifest(**payload)


def test_manifest_forbids_extra_fields() -> None:
    payload = _example_payload()
    payload["rogue"] = "nope"
    with pytest.raises(ValidationError):
        SessionManifest(**payload)


# ---------------------------------------------------------------------------
# ended_at semantics
# ---------------------------------------------------------------------------


def test_manifest_ended_at_none_means_in_progress() -> None:
    m = SessionManifest(**_example_payload(ended_at=None))
    assert m.ended_at is None


def test_manifest_ended_at_populated_means_complete() -> None:
    m = SessionManifest(**_example_payload(ended_at=_ENDED))
    assert m.ended_at == _ENDED


def test_manifest_ended_at_missing_defaults_to_none() -> None:
    payload = _example_payload()
    payload.pop("ended_at")
    m = SessionManifest(**payload)
    assert m.ended_at is None


# ---------------------------------------------------------------------------
# Typed baselines / summary (v0.2.0)
# ---------------------------------------------------------------------------


def test_manifest_baselines_is_typed_Baseline_model() -> None:
    from halcytone_contracts.baseline import Baseline, StreamBaseline

    m = SessionManifest(**_example_payload())
    assert isinstance(m.baselines, Baseline)
    for sb in m.baselines.streams.values():
        assert isinstance(sb, StreamBaseline)


def test_manifest_summary_is_typed_SessionSummary_model() -> None:
    from halcytone_contracts.summary import SessionSummary

    m = SessionManifest(**_example_payload())
    assert isinstance(m.summary, SessionSummary)


def test_manifest_rejects_dict_shaped_baselines() -> None:
    """Breaking-change migration helper: dict[str, float] no longer valid."""
    payload = _example_payload()
    payload["baselines"] = {"hrv.rmssd": 48.3, "breath.rate": 6.2}
    with pytest.raises(ValidationError):
        SessionManifest(**payload)


def test_manifest_rejects_dict_shaped_summary() -> None:
    """Breaking-change migration helper: dict[str, float] no longer valid."""
    payload = _example_payload()
    payload["summary"] = {"mean_hr": 62.1, "mean_presence": 0.72}
    with pytest.raises(ValidationError):
        SessionManifest(**payload)


def test_manifest_rejects_baseline_with_unknown_stream_key() -> None:
    """Baseline.streams validation fires through the manifest."""
    payload = _example_payload()
    payload["baselines"]["streams"]["not.a.real.stream"] = {
        "mean": 0.0,
        "stddev": 0.0,
        "sample_count": 1,
    }
    with pytest.raises(ValidationError) as exc_info:
        SessionManifest(**payload)
    assert "not.a.real.stream" in str(exc_info.value)


# ---------------------------------------------------------------------------
# YAML round-trip
# ---------------------------------------------------------------------------


def test_manifest_yaml_roundtrip_preserves_fields() -> None:
    original = SessionManifest(**_example_payload())
    as_yaml = yaml.safe_dump(original.model_dump(mode="json"), sort_keys=True)
    reloaded = SessionManifest(**yaml.safe_load(as_yaml))
    assert reloaded == original


def test_manifest_yaml_roundtrip_with_populated_baseline_and_summary() -> None:
    """Full v0.2.0 manifest shape — multi-stream baseline + every summary field."""
    original = SessionManifest(**_example_payload())
    as_yaml = yaml.safe_dump(original.model_dump(mode="json"), sort_keys=True)
    reloaded = SessionManifest(**yaml.safe_load(as_yaml))
    assert reloaded == original
    assert len(reloaded.baselines.streams) == 3
    assert reloaded.summary.summary_schema_version == 1
    assert reloaded.summary.total_annotations == 3


def test_manifest_yaml_roundtrip_with_in_progress_session() -> None:
    original = SessionManifest(**_example_payload(ended_at=None))
    as_yaml = yaml.safe_dump(original.model_dump(mode="json"), sort_keys=True)
    reloaded = SessionManifest(**yaml.safe_load(as_yaml))
    assert reloaded == original
    assert reloaded.ended_at is None


# ---------------------------------------------------------------------------
# Schema drift detection
# ---------------------------------------------------------------------------


_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _REPO_ROOT / "halcytone_contracts" / "bundles" / "manifest.schema.json"


def test_manifest_schema_file_is_checked_in() -> None:
    assert _SCHEMA_PATH.exists(), f"expected {_SCHEMA_PATH} to be checked in"


def test_manifest_schema_matches_model_json_schema() -> None:
    on_disk = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    assert on_disk == SessionManifest.model_json_schema()


def test_manifest_schema_is_packaged() -> None:
    """The generated schema ships inside the installed package."""
    data = (
        resources.files("halcytone_contracts.bundles")
        .joinpath("manifest.schema.json")
        .read_bytes()
    )
    assert data == _SCHEMA_PATH.read_bytes()
