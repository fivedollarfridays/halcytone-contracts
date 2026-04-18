"""Session-baseline contract: per-stream statistics captured during the
60s quiet-capture window at session start.

`StreamBaseline` holds one stream's summary statistics (`mean`, `stddev`,
`sample_count`); `Baseline` is the per-session envelope keyed by reserved
stream name. Dict keys are validated against `RESERVED_STREAMS` at parse
time so halcytone-core can't silently record a baseline for a nonexistent
sensor — unknown keys raise with a message naming the offending stream(s).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from halcytone_contracts.signals import RESERVED_STREAMS


class StreamBaseline(BaseModel):
    """One stream's summary statistics over the quiet-capture window."""

    model_config = ConfigDict(frozen=False, extra="forbid")

    mean: float
    stddev: float = Field(ge=0.0)
    sample_count: int = Field(ge=1)


class Baseline(BaseModel):
    """Per-session baseline: stream -> StreamBaseline, plus capture window.

    `streams` must contain at least one entry — a session that captured no
    baselines is not representable in v0.2.0 (the manifest field is
    non-optional by design; revisit if a use case emerges). Every dict key
    must be a reserved name from `halcytone_contracts.signals.RESERVED_STREAMS`;
    unknown keys raise `ValidationError` with a sorted list of the
    offenders in the message.
    """

    model_config = ConfigDict(frozen=False, extra="forbid")

    streams: dict[str, StreamBaseline]
    duration_s: int = Field(ge=1)
    captured_at: datetime

    @field_validator("streams")
    @classmethod
    def _streams_keyed_by_reserved_name(
        cls, v: dict[str, StreamBaseline]
    ) -> dict[str, StreamBaseline]:
        if not v:
            raise ValueError("streams must contain at least one entry")
        unknown = [k for k in v if k not in RESERVED_STREAMS]
        if unknown:
            raise ValueError(
                "unknown stream name(s) not in RESERVED_STREAMS: "
                + ", ".join(sorted(unknown))
            )
        return v


__all__ = ["Baseline", "StreamBaseline"]
