"""Top-level export surface for `halcytone_contracts`.

Fleet consumers `from halcytone_contracts import SignalPacket, StateVector, ...`
— every symbol the backlog promises as public is asserted here. The pyproject
version string is also cross-checked against `__contract_version__` so drift
between the two cannot ship silently.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import halcytone_contracts as hc

_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _pyproject_version() -> str:
    data = tomllib.loads(_PYPROJECT.read_text(encoding="utf-8"))
    return data["project"]["version"]


class TestContractVersion:
    def test_is_string(self) -> None:
        assert isinstance(hc.__contract_version__, str)

    def test_matches_pyproject(self) -> None:
        assert hc.__contract_version__ == _pyproject_version()

    def test_matches_legacy_version_alias(self) -> None:
        # `__version__` already existed in T1.1; keep them in lockstep.
        assert hc.__version__ == hc.__contract_version__


class TestRequiredSchemaVersion:
    def test_re_exported_at_top_level(self) -> None:
        assert hasattr(hc, "REQUIRED_SCHEMA_VERSION")

    def test_equals_storage_schema_version(self) -> None:
        from halcytone_contracts.storage import SCHEMA_VERSION

        assert hc.REQUIRED_SCHEMA_VERSION == SCHEMA_VERSION

    def test_is_int(self) -> None:
        assert isinstance(hc.REQUIRED_SCHEMA_VERSION, int)

    def test_schema_version_also_exported(self) -> None:
        from halcytone_contracts.storage import SCHEMA_VERSION

        assert hc.SCHEMA_VERSION == SCHEMA_VERSION


REQUIRED_EXPORTS = (
    "SignalPacket",
    "StreamSpec",
    "RESERVED_STREAMS",
    "StateVector",
    "SessionStart",
    "SessionStop",
    "Annotation",
    "MapperConfigUpdate",
    "SessionManifest",
    "SCHEMA_VERSION",
    "REQUIRED_SCHEMA_VERSION",
    "__contract_version__",
    "validate_stream_roster",
    "check_contract_version",
    "ContractError",
)


class TestPublicSurface:
    def test_all_declares_required_exports(self) -> None:
        assert hasattr(hc, "__all__")
        missing = set(REQUIRED_EXPORTS) - set(hc.__all__)
        assert not missing, f"missing from __all__: {sorted(missing)}"

    def test_every_required_export_is_attribute(self) -> None:
        missing = [name for name in REQUIRED_EXPORTS if not hasattr(hc, name)]
        assert not missing, f"not importable: {missing}"

    def test_models_identity_matches_submodules(self) -> None:
        from halcytone_contracts.bundles.manifest import SessionManifest
        from halcytone_contracts.session import (
            Annotation,
            MapperConfigUpdate,
            SessionStart,
            SessionStop,
        )
        from halcytone_contracts.signals import (
            RESERVED_STREAMS,
            SignalPacket,
            StreamSpec,
        )
        from halcytone_contracts.state import StateVector

        assert hc.SignalPacket is SignalPacket
        assert hc.StreamSpec is StreamSpec
        assert hc.RESERVED_STREAMS is RESERVED_STREAMS
        assert hc.StateVector is StateVector
        assert hc.SessionStart is SessionStart
        assert hc.SessionStop is SessionStop
        assert hc.Annotation is Annotation
        assert hc.MapperConfigUpdate is MapperConfigUpdate
        assert hc.SessionManifest is SessionManifest
