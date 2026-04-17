"""Drift guardrails: runtime checks the fleet uses to detect contract mismatch.

Two helpers + one exception class:

* `ContractError` — raised when a check fails hard (missing streams, major-
  version mismatch, malformed version). Subclasses `RuntimeError` so it's
  catchable at the top of long-running services without swallowing
  `KeyboardInterrupt` / `SystemExit`.
* `validate_stream_roster(published, required)` — raises when a publisher
  advertises a stream set that does not cover what a consumer requires. The
  exception message names the missing streams so operators can diff rosters
  without re-running a debugger.
* `check_contract_version(consumer_version)` — enforces the fleet's semver
  policy against `__contract_version__`:

    | Delta          | Action                        |
    |----------------|-------------------------------|
    | exact or patch | no-op                         |
    | minor          | `warnings.warn(UserWarning)`  |
    | major          | raise `ContractError`         |
    | malformed      | raise `ContractError`         |

  Patch-only changes are strictly backward compatible, so we don't even warn;
  minor additions are additive-only by policy and warn so operators can opt
  into a re-pin; major bumps are breaking and must be an outright failure.
"""

from __future__ import annotations

import warnings
from collections.abc import Iterable


class ContractError(RuntimeError):
    """Raised when a runtime drift check fails hard."""


def validate_stream_roster(
    published: Iterable[str],
    required: Iterable[str],
) -> None:
    """Check that `published` covers every name in `required`.

    Returns ``None`` when ``set(published) ⊇ set(required)``. Raises
    `ContractError` listing the missing names otherwise.
    """
    published_set = set(published)
    required_set = set(required)
    missing = required_set - published_set
    if missing:
        missing_sorted = sorted(missing)
        raise ContractError(
            "stream roster drift: publisher is missing required stream(s): "
            f"{missing_sorted}"
        )
    return None


def _parse_semver(version: str) -> tuple[int, int, int]:
    if not isinstance(version, str) or not version:
        raise ContractError(f"invalid version string: {version!r}")
    parts = version.split(".")
    if len(parts) != 3:
        raise ContractError(
            f"invalid version string: {version!r}: expected 'major.minor.patch'"
        )
    try:
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError as exc:
        raise ContractError(f"invalid version string: {version!r}") from exc


def check_contract_version(consumer_version: str) -> None:
    """Enforce semver policy for a consumer's pinned contract version.

    Compares ``consumer_version`` to ``halcytone_contracts.__contract_version__``
    (imported lazily to avoid a circular import at module load). Hard-fails
    on major-version mismatch, warns on minor-version mismatch, is a no-op
    otherwise.
    """
    from halcytone_contracts import __contract_version__

    c_major, c_minor, _c_patch = _parse_semver(consumer_version)
    p_major, p_minor, _p_patch = _parse_semver(__contract_version__)

    if c_major != p_major:
        raise ContractError(
            f"contract major-version mismatch: consumer pinned {consumer_version}, "
            f"package is {__contract_version__}"
        )
    if c_minor != p_minor:
        warnings.warn(
            f"contract minor-version mismatch: consumer pinned {consumer_version}, "
            f"package is {__contract_version__}",
            UserWarning,
            stacklevel=2,
        )
    return None


__all__ = [
    "ContractError",
    "check_contract_version",
    "validate_stream_roster",
]
