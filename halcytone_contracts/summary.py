"""Session-summary contract: end-of-session aggregate statistics.

`SessionSummary` is the typed payload halcytone-publish writes into
`SessionManifest.summary` once a session ends. Numeric fields cover the
aggregate statistics the fleet actually consumes today; range-bounded
fields stay in `[0, 1]` so downstream readers (AgentGrounds, HUD review,
analytics) can trust the bounds without re-checking.

Bumping `summary_schema_version`
--------------------------------
The first field is `summary_schema_version: int` (default `1`, `ge=1`) so
consumers can key logic off the shape. To evolve the contract:

1. Add the new field (or change a type) on `SessionSummary`.
2. Increment the default of `summary_schema_version` by 1.
3. Consumers branch on `summary.summary_schema_version` — older bundles
   keep their original integer and read with the old code path; new
   bundles carry the bumped version and unlock the new shape.

A bundle written under the current contract serializes
`summary_schema_version: 1` into its YAML/JSON payload explicitly — the
default isn't a runtime fallback during deserialization; it's a
construct-time convenience. That means old bundles **on disk** already
carry their version number, and will keep parsing under any future
`SessionSummary` whose default has bumped higher. Do not remove the
default when bumping — the ergonomics during construction matter, and
the back-compat guarantee comes from the serialized value, not the
default.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from halcytone_contracts.signals import Unit as _Unit


class SessionSummary(BaseModel):
    """End-of-session aggregate statistics written into `manifest.summary`."""

    model_config = ConfigDict(frozen=False, extra="forbid")

    summary_schema_version: int = Field(default=1, ge=1)

    mean_hr: float
    mean_hrv_rmssd: float
    mean_breath_rate: float
    mean_breath_depth: _Unit
    mean_eeg_alpha: _Unit
    mean_eeg_theta: _Unit
    mean_overall_presence: _Unit
    peak_heart_breath_coherence: _Unit
    total_annotations: int = Field(ge=0)


__all__ = ["SessionSummary"]
