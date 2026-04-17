"""Tests for halcytone_contracts.bundles.manifest."""

from __future__ import annotations

import json
import subprocess
import sys
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


def _example_payload(*, ended_at: datetime | None = _ENDED) -> dict:
    return {
        "session_id": _EXAMPLE_ID,
        "started_at": _STARTED,
        "ended_at": ended_at,
        "duration_s": 1945,
        "sensors": ["ganglion-01", "emotibit-01", "stemoscope-01"],
        "baselines": {"hrv_rmssd": 48.3, "breath_rate": 6.2, "eda_level": 2.1},
        "summary": {"mean_hr": 62.1, "mean_hrv": 51.7, "mean_presence": 0.72},
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
    assert m.baselines["hrv_rmssd"] == 48.3
    assert m.summary["mean_hr"] == 62.1
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
# YAML round-trip
# ---------------------------------------------------------------------------


def test_manifest_yaml_roundtrip_preserves_fields() -> None:
    original = SessionManifest(**_example_payload())
    as_yaml = yaml.safe_dump(original.model_dump(mode="json"), sort_keys=True)
    reloaded = SessionManifest(**yaml.safe_load(as_yaml))
    assert reloaded == original


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
_REGEN_SCRIPT = _REPO_ROOT / "scripts" / "regen_manifest_schema.py"


def test_manifest_schema_file_is_checked_in() -> None:
    assert _SCHEMA_PATH.exists(), f"expected {_SCHEMA_PATH} to be checked in"


def test_manifest_schema_matches_model_json_schema() -> None:
    on_disk = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    assert on_disk == SessionManifest.model_json_schema()


def test_regen_script_output_is_byte_equal_to_checked_in_file() -> None:
    result = subprocess.run(
        [sys.executable, str(_REGEN_SCRIPT), "--stdout"],
        capture_output=True,
        check=True,
    )
    expected = _SCHEMA_PATH.read_bytes()
    assert result.stdout == expected, "regen output drifted from checked-in schema"


def test_manifest_schema_is_packaged() -> None:
    """The generated schema ships inside the installed package."""
    data = (
        resources.files("halcytone_contracts.bundles")
        .joinpath("manifest.schema.json")
        .read_bytes()
    )
    assert data == _SCHEMA_PATH.read_bytes()
