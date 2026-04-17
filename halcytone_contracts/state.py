"""State-layer contract: `StateVector`, the per-tick fused frame.

halcytone-core consumes `SignalPacket`s, aligns them, and emits one
`StateVector` per fusion tick (target cadence: 200 Hz). Every downstream
module (audio, HUD, publish) reads `StateVector`s, never raw signals.

The model is a **flat struct by choice** — consumers want one frame per
tick, not a bag of streams to re-align. Core aligns once, emits a flat
record, done. No nested pydantic sub-models live in this file.

Each record is logged one-per-line to `state.jsonl` inside the session
bundle (see README §"Session bundle"). `model_dump_json()` produces a
single-line JSON string suitable for JSONL; `model_validate_json()`
parses it back losslessly.

Range-bounded fields (phase, depth, coherence, presence, normalized EEG
band powers, and every `*_quality` score) are validated in `[0, 1]` so
downstream code can trust bounds without re-checking. Quality scores are
uniform across modalities by design — a consumer comparing
`breath_quality` to `eeg_quality` is asking a meaningful question.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from halcytone_contracts.session import SessionId
from halcytone_contracts.signals import Unit as _Unit


class StateVector(BaseModel):
    """Fused per-tick state emitted by halcytone-core's fusion layer."""

    model_config = ConfigDict(frozen=False, extra="forbid")

    t_ns: int = Field(ge=0)
    session_id: SessionId

    # breath
    breath_phase: _Unit
    breath_rate: float
    breath_depth: _Unit
    breath_quality: _Unit

    # cardiovascular
    heart_rate: float
    hrv_rmssd: float
    hrv_quality: _Unit

    # autonomic
    eda_level: float
    eda_phasic: float

    # neural (Ganglion band power, normalized 0..1)
    eeg_alpha: _Unit
    eeg_theta: _Unit
    eeg_beta: _Unit
    eeg_delta: _Unit
    eeg_gamma: _Unit
    eeg_quality: _Unit

    # composite
    heart_breath_coherence: _Unit
    overall_presence: _Unit


__all__ = ["StateVector"]
