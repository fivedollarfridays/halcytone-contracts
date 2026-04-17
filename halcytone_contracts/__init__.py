"""Top-level public surface for the halcytone-contracts package.

Everything a fleet repo is allowed to depend on is re-exported here so that
sibling repos can write ``from halcytone_contracts import SignalPacket`` and
treat the submodule layout as an implementation detail.

`__contract_version__` is the authoritative semver string for this package
and must stay in lockstep with the version declared in ``pyproject.toml``
(`tests/test_exports.py` enforces the invariant at test time).
"""

from __future__ import annotations

from halcytone_contracts.bundles.manifest import SessionManifest
from halcytone_contracts.drift import (
    ContractError,
    check_contract_version,
    validate_stream_roster,
)
from halcytone_contracts.session import (
    Annotation,
    MapperConfigUpdate,
    SessionStart,
    SessionStop,
)
from halcytone_contracts.signals import RESERVED_STREAMS, SignalPacket, StreamSpec
from halcytone_contracts.state import StateVector
from halcytone_contracts.storage import REQUIRED_SCHEMA_VERSION, SCHEMA_VERSION

__contract_version__: str = "0.1.0"
__version__: str = __contract_version__

__all__ = [
    "Annotation",
    "ContractError",
    "MapperConfigUpdate",
    "REQUIRED_SCHEMA_VERSION",
    "RESERVED_STREAMS",
    "SCHEMA_VERSION",
    "SessionManifest",
    "SessionStart",
    "SessionStop",
    "SignalPacket",
    "StateVector",
    "StreamSpec",
    "__contract_version__",
    "__version__",
    "check_contract_version",
    "validate_stream_roster",
]
