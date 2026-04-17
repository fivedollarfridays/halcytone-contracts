"""Session-layer contracts: control messages + canonical session-id format.

The four pydantic v2 models (`SessionStart`, `SessionStop`, `Annotation`,
`MapperConfigUpdate`) describe the Python messages halcytone-core publishes
on its in-process asyncio bus during a session's lifecycle (README §"Session
protocol → Control messages"). The bus itself lives in halcytone-core; this
package owns only the shapes.

Session-id format: ``{YYYYMMDD}-{HHMMSS}-{slug4}`` (e.g. ``20260417-143022-k7m2``).
`SESSION_ID_REGEX` is the single source of truth for that format — the
manifest in `bundles/manifest.py` (T1.6) validates `session_id` against it,
and `SessionStart` enforces it on inbound messages.

Helpers:
  * `format_session_id(dt, slug)` — build an id from a naive datetime + slug
  * `parse_session_id(s)` — inverse of `format_session_id`; raises on invalid
  * `new_session_id()` — generate a fresh, regex-valid id (UTC wall-clock +
    monotonic-counter slug so consecutive calls in a tight loop cannot collide)
"""

from __future__ import annotations

import random
import re
import string
import threading
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

_SLUG_ALPHABET = string.digits + string.ascii_lowercase  # base36
_SLUG_LENGTH = 4
_SLUG_SPACE = len(_SLUG_ALPHABET) ** _SLUG_LENGTH  # 36**4 == 1_679_616
_DT_STRFTIME = "%Y%m%d-%H%M%S"

SESSION_ID_REGEX: re.Pattern[str] = re.compile(
    rf"^\d{{8}}-\d{{6}}-[{re.escape(_SLUG_ALPHABET)}]{{{_SLUG_LENGTH}}}$"
)
_SLUG_REGEX = re.compile(rf"^[{re.escape(_SLUG_ALPHABET)}]{{{_SLUG_LENGTH}}}$")


def _to_base36(n: int, width: int) -> str:
    out: list[str] = []
    for _ in range(width):
        n, r = divmod(n, 36)
        out.append(_SLUG_ALPHABET[r])
    return "".join(reversed(out))


_slug_lock = threading.Lock()
_slug_counter = random.randrange(_SLUG_SPACE)


def _next_slug() -> str:
    global _slug_counter
    with _slug_lock:
        value = _slug_counter
        _slug_counter = (_slug_counter + 1) % _SLUG_SPACE
    return _to_base36(value, _SLUG_LENGTH)


def format_session_id(dt: datetime, slug: str) -> str:
    """Assemble a canonical session-id from a datetime + 4-char base36 slug."""
    if not _SLUG_REGEX.fullmatch(slug):
        raise ValueError(
            f"invalid slug {slug!r}: must be {_SLUG_LENGTH} chars from [0-9a-z]"
        )
    return f"{dt.strftime(_DT_STRFTIME)}-{slug}"


def parse_session_id(s: str) -> tuple[datetime, str]:
    """Inverse of `format_session_id`. Raises ValueError on malformed input."""
    if not isinstance(s, str) or not SESSION_ID_REGEX.fullmatch(s):
        raise ValueError(f"invalid session_id {s!r}: expected {{YYYYMMDD}}-{{HHMMSS}}-{{slug4}}")
    date_str, time_str, slug = s.split("-")
    dt = datetime.strptime(f"{date_str}-{time_str}", _DT_STRFTIME)
    return dt, slug


def new_session_id() -> str:
    """Return a fresh session-id using UTC wall-clock + counter-driven slug."""
    dt = datetime.now(UTC).replace(tzinfo=None)
    return format_session_id(dt, _next_slug())


class SessionStart(BaseModel):
    """Control message: begin a session. `session_id` must match the canonical regex."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    config: dict[str, Any]

    @field_validator("session_id")
    @classmethod
    def _validate_session_id(cls, v: str) -> str:
        if not SESSION_ID_REGEX.fullmatch(v):
            raise ValueError(f"invalid session_id {v!r}")
        return v


class SessionStop(BaseModel):
    """Control message: end the current session. No payload."""

    model_config = ConfigDict(extra="forbid")


class Annotation(BaseModel):
    """User- or module-emitted annotation tied to a monotonic ns timestamp."""

    model_config = ConfigDict(extra="forbid")

    t_ns: int
    label: str
    data: dict[str, Any]


class MapperConfigUpdate(BaseModel):
    """Live parameter-mapper retuning event carried on the same bus."""

    model_config = ConfigDict(extra="forbid")

    params: dict[str, Any]


__all__ = [
    "SESSION_ID_REGEX",
    "Annotation",
    "MapperConfigUpdate",
    "SessionStart",
    "SessionStop",
    "format_session_id",
    "new_session_id",
    "parse_session_id",
]
