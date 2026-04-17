"""Tests for halcytone_contracts.signals."""

from __future__ import annotations

import dataclasses
import json

import pytest
from pydantic import ValidationError

from halcytone_contracts.signals import (
    RESERVED_STREAMS,
    SignalPacket,
    StreamSpec,
)

# ---------------------------------------------------------------------------
# SignalPacket
# ---------------------------------------------------------------------------


def _sample_packet_kwargs() -> dict:
    return {
        "sensor_id": "ganglion-01",
        "stream": "eeg.ch1",
        "t_ns": 1_700_000_000_000_000_000,
        "values": [0.1, 0.2, 0.3],
        "quality": 0.9,
    }


def test_signal_packet_has_all_required_fields() -> None:
    packet = SignalPacket(**_sample_packet_kwargs())
    assert packet.sensor_id == "ganglion-01"
    assert packet.stream == "eeg.ch1"
    assert packet.t_ns == 1_700_000_000_000_000_000
    assert packet.values == [0.1, 0.2, 0.3]
    assert packet.quality == 0.9


def test_signal_packet_field_set() -> None:
    expected = {"sensor_id", "stream", "t_ns", "values", "quality"}
    assert set(SignalPacket.model_fields.keys()) == expected


@pytest.mark.parametrize("bad_quality", [-0.1, 1.1, -1.0, 2.0])
def test_signal_packet_quality_out_of_range_raises(bad_quality: float) -> None:
    kwargs = _sample_packet_kwargs()
    kwargs["quality"] = bad_quality
    with pytest.raises(ValidationError):
        SignalPacket(**kwargs)


@pytest.mark.parametrize("good_quality", [0.0, 0.5, 1.0])
def test_signal_packet_quality_boundary_values_accepted(good_quality: float) -> None:
    kwargs = _sample_packet_kwargs()
    kwargs["quality"] = good_quality
    packet = SignalPacket(**kwargs)
    assert packet.quality == good_quality


def test_signal_packet_json_round_trip_preserves_all_fields() -> None:
    original = SignalPacket(**_sample_packet_kwargs())
    as_json = original.model_dump_json()
    payload = json.loads(as_json)
    restored = SignalPacket.model_validate(payload)
    assert restored == original
    assert restored.sensor_id == original.sensor_id
    assert restored.stream == original.stream
    assert restored.t_ns == original.t_ns
    assert restored.values == original.values
    assert restored.quality == original.quality


def test_signal_packet_rejects_missing_fields() -> None:
    with pytest.raises(ValidationError):
        SignalPacket(sensor_id="x", stream="y", t_ns=1, values=[0.0])  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# StreamSpec
# ---------------------------------------------------------------------------


def test_stream_spec_is_frozen_dataclass() -> None:
    assert dataclasses.is_dataclass(StreamSpec)
    params = getattr(StreamSpec, "__dataclass_params__")
    assert params.frozen is True


def test_stream_spec_has_all_required_fields() -> None:
    field_names = {f.name for f in dataclasses.fields(StreamSpec)}
    expected = {
        "name",
        "domain",
        "sample_rate_hz",
        "channel_count",
        "dtype",
        "derived",
        "archive_only",
    }
    assert field_names == expected


def test_stream_spec_is_immutable() -> None:
    spec = StreamSpec(
        name="eeg.ch1",
        domain="eeg",
        sample_rate_hz=200.0,
        channel_count=1,
        dtype="float32",
        derived=False,
        archive_only=False,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.name = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# RESERVED_STREAMS registry
# ---------------------------------------------------------------------------


REQUIRED_STREAM_NAMES = {
    "eeg.ch1",
    "eeg.ch2",
    "eeg.ch3",
    "eeg.ch4",
    "eeg.alpha",
    "eeg.theta",
    "eeg.beta",
    "eeg.delta",
    "eeg.gamma",
    "ppg",
    "hrv.rmssd",
    "hrv.sdnn",
    "eda",
    "skin_temp",
    "imu.accel",
    "imu.gyro",
    "breath.acoustic",
    "breath.envelope",
    "breath.rate",
    "breath.phase",
    "breath.depth",
}


def test_reserved_streams_is_dict_of_stream_specs() -> None:
    assert isinstance(RESERVED_STREAMS, dict)
    for value in RESERVED_STREAMS.values():
        assert isinstance(value, StreamSpec)


def test_reserved_streams_covers_every_readme_name() -> None:
    missing = REQUIRED_STREAM_NAMES - set(RESERVED_STREAMS.keys())
    assert not missing, f"Missing reserved streams: {sorted(missing)}"


def test_reserved_streams_has_no_unexpected_entries() -> None:
    unexpected = set(RESERVED_STREAMS.keys()) - REQUIRED_STREAM_NAMES
    assert not unexpected, f"Unexpected reserved streams: {sorted(unexpected)}"


def test_reserved_streams_keys_match_spec_names() -> None:
    for key, spec in RESERVED_STREAMS.items():
        assert key == spec.name, f"Key {key!r} != spec.name {spec.name!r}"


def test_reserved_streams_no_duplicate_names() -> None:
    names = [spec.name for spec in RESERVED_STREAMS.values()]
    assert len(names) == len(set(names))


def test_reserved_streams_positive_sample_rate_and_channel_count() -> None:
    for spec in RESERVED_STREAMS.values():
        assert spec.sample_rate_hz > 0, f"{spec.name} has non-positive sample_rate_hz"
        assert spec.channel_count >= 1, f"{spec.name} has channel_count < 1"


DERIVED_EXPECTED = {
    "eeg.ch1": False,
    "eeg.ch2": False,
    "eeg.ch3": False,
    "eeg.ch4": False,
    "eeg.alpha": True,
    "eeg.theta": True,
    "eeg.beta": True,
    "eeg.delta": True,
    "eeg.gamma": True,
    "ppg": False,
    "hrv.rmssd": True,
    "hrv.sdnn": True,
    "eda": False,
    "skin_temp": False,
    "imu.accel": False,
    "imu.gyro": False,
    "breath.acoustic": False,
    "breath.envelope": True,
    "breath.rate": True,
    "breath.phase": True,
    "breath.depth": True,
}


@pytest.mark.parametrize("name,expected_derived", sorted(DERIVED_EXPECTED.items()))
def test_reserved_streams_derived_flag(name: str, expected_derived: bool) -> None:
    assert RESERVED_STREAMS[name].derived is expected_derived


def test_breath_acoustic_is_archive_only() -> None:
    assert RESERVED_STREAMS["breath.acoustic"].archive_only is True


def test_non_acoustic_streams_are_not_archive_only() -> None:
    for name, spec in RESERVED_STREAMS.items():
        if name == "breath.acoustic":
            continue
        assert spec.archive_only is False, f"{name} unexpectedly archive_only"


def test_imu_streams_have_three_channels() -> None:
    assert RESERVED_STREAMS["imu.accel"].channel_count == 3
    assert RESERVED_STREAMS["imu.gyro"].channel_count == 3


def test_breath_acoustic_is_high_rate() -> None:
    assert RESERVED_STREAMS["breath.acoustic"].sample_rate_hz >= 16_000


def test_domains_cover_expected_modalities() -> None:
    domains = {spec.domain for spec in RESERVED_STREAMS.values()}
    assert {"eeg", "ppg", "hrv", "eda", "skin_temp", "imu", "breath"} <= domains
