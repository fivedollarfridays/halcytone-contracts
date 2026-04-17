"""Signal-layer contracts: wire shape, stream registry, reserved names.

Pure schema — no I/O, no LSL. `SignalPacket` is the pydantic v2 model every
sensor adapter emits; `StreamSpec` describes a named stream in the registry;
`RESERVED_STREAMS` enumerates every stream name the Halcytone fleet agrees
on for v1 (see README §"Stream naming convention").
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

Unit = Annotated[float, Field(ge=0.0, le=1.0)]
"""A float in ``[0, 1]``. Single source of truth for every normalized /
quality-score field across the package (reused by `state.StateVector`)."""


class SignalPacket(BaseModel):
    """Python-level view of one LSL sample emitted by a sensor adapter."""

    model_config = ConfigDict(frozen=False, extra="forbid")

    sensor_id: str = Field(min_length=1)
    stream: str = Field(min_length=1)
    t_ns: int = Field(ge=0)
    values: list[float]
    quality: Unit


@dataclass(frozen=True, slots=True)
class StreamSpec:
    """Registry entry describing a named stream in `RESERVED_STREAMS`."""

    name: str
    domain: str
    sample_rate_hz: float
    channel_count: int
    dtype: str
    derived: bool
    archive_only: bool


def _spec(
    name: str,
    domain: str,
    sample_rate_hz: float,
    channel_count: int = 1,
    dtype: str = "float32",
    derived: bool = False,
    archive_only: bool = False,
) -> StreamSpec:
    return StreamSpec(
        name=name,
        domain=domain,
        sample_rate_hz=sample_rate_hz,
        channel_count=channel_count,
        dtype=dtype,
        derived=derived,
        archive_only=archive_only,
    )


_EEG_RAW_HZ = 200.0          # OpenBCI Ganglion raw channel rate
_EEG_BAND_HZ = 10.0          # band-power updates from sensor adapter
_PPG_HZ = 25.0               # EmotiBit PPG
_HRV_HZ = 1.0                # 30s rolling window updates
_EDA_HZ = 15.0               # EmotiBit EDA
_SKIN_TEMP_HZ = 7.5          # EmotiBit skin temperature
_IMU_HZ = 25.0               # EmotiBit accel/gyro
_BREATH_ACOUSTIC_HZ = 48_000.0   # Stemoscope raw audio
_BREATH_ENVELOPE_HZ = 100.0      # RMS envelope, primary live signal
_BREATH_DERIVED_HZ = 10.0        # rate/phase/depth from envelope


_EEG_CHANNELS: tuple[StreamSpec, ...] = tuple(
    _spec(f"eeg.ch{i}", "eeg", _EEG_RAW_HZ) for i in range(1, 5)
)

_EEG_BAND_POWERS: tuple[StreamSpec, ...] = tuple(
    _spec(f"eeg.{band}", "eeg", _EEG_BAND_HZ, derived=True)
    for band in ("alpha", "theta", "beta", "delta", "gamma")
)

_BODY_STREAMS: tuple[StreamSpec, ...] = (
    _spec("ppg", "ppg", _PPG_HZ),
    _spec("hrv.rmssd", "hrv", _HRV_HZ, derived=True),
    _spec("hrv.sdnn", "hrv", _HRV_HZ, derived=True),
    _spec("eda", "eda", _EDA_HZ),
    _spec("skin_temp", "skin_temp", _SKIN_TEMP_HZ),
    _spec("imu.accel", "imu", _IMU_HZ, channel_count=3),
    _spec("imu.gyro", "imu", _IMU_HZ, channel_count=3),
)

_BREATH_STREAMS: tuple[StreamSpec, ...] = (
    _spec("breath.acoustic", "breath", _BREATH_ACOUSTIC_HZ, archive_only=True),
    _spec("breath.envelope", "breath", _BREATH_ENVELOPE_HZ, derived=True),
    _spec("breath.rate", "breath", _BREATH_DERIVED_HZ, derived=True),
    _spec("breath.phase", "breath", _BREATH_DERIVED_HZ, derived=True),
    _spec("breath.depth", "breath", _BREATH_DERIVED_HZ, derived=True),
)


RESERVED_STREAMS: dict[str, StreamSpec] = {
    spec.name: spec
    for spec in (*_EEG_CHANNELS, *_EEG_BAND_POWERS, *_BODY_STREAMS, *_BREATH_STREAMS)
}


__all__ = ["RESERVED_STREAMS", "SignalPacket", "StreamSpec"]
