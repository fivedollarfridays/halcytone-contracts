"""Drift-helper tests: validate_stream_roster + check_contract_version.

These helpers are the fleet's runtime line of defense against a downstream
repo pinning to a contract version that no longer matches what the publisher
is producing. `validate_stream_roster` raises when a publisher's advertised
stream set is missing one required by a consumer; `check_contract_version`
enforces the semver policy documented in README §"Versioning".
"""

from __future__ import annotations

import warnings

import pytest

from halcytone_contracts import (
    ContractError,
    __contract_version__,
    check_contract_version,
    validate_stream_roster,
)


class TestContractError:
    def test_is_exception_subclass(self) -> None:
        assert issubclass(ContractError, Exception)

    def test_is_runtime_error_subclass(self) -> None:
        assert issubclass(ContractError, RuntimeError)

    def test_carries_message(self) -> None:
        exc = ContractError("boom")
        assert str(exc) == "boom"


class TestValidateStreamRoster:
    def test_exact_match_is_noop(self) -> None:
        required = ["eeg.ch1", "ppg"]
        assert validate_stream_roster(required, required) is None

    def test_superset_is_noop(self) -> None:
        published = ["eeg.ch1", "eeg.ch2", "ppg", "eda"]
        required = ["eeg.ch1", "ppg"]
        assert validate_stream_roster(published, required) is None

    def test_empty_required_is_noop(self) -> None:
        assert validate_stream_roster(["eeg.ch1"], []) is None
        assert validate_stream_roster([], []) is None

    def test_accepts_sets(self) -> None:
        assert validate_stream_roster({"a", "b", "c"}, {"a"}) is None

    def test_accepts_generators(self) -> None:
        published = (s for s in ["a", "b", "c"])
        required = (s for s in ["a", "b"])
        assert validate_stream_roster(published, required) is None

    def test_single_missing_raises_contract_error(self) -> None:
        with pytest.raises(ContractError):
            validate_stream_roster(["eeg.ch1"], ["eeg.ch1", "ppg"])

    def test_missing_stream_name_appears_in_message(self) -> None:
        with pytest.raises(ContractError) as exc_info:
            validate_stream_roster(["eeg.ch1"], ["eeg.ch1", "ppg"])
        assert "ppg" in str(exc_info.value)

    def test_multiple_missing_all_named_in_message(self) -> None:
        with pytest.raises(ContractError) as exc_info:
            validate_stream_roster(["eeg.ch1"], ["eeg.ch1", "ppg", "eda", "skin_temp"])
        msg = str(exc_info.value)
        assert "ppg" in msg
        assert "eda" in msg
        assert "skin_temp" in msg

    def test_message_does_not_mention_published_only_streams(self) -> None:
        with pytest.raises(ContractError) as exc_info:
            validate_stream_roster(["extra_stream", "eeg.ch1"], ["eeg.ch1", "ppg"])
        assert "extra_stream" not in str(exc_info.value)

    def test_all_missing_raises(self) -> None:
        with pytest.raises(ContractError):
            validate_stream_roster([], ["eeg.ch1"])


class TestCheckContractVersion:
    def test_exact_match_is_noop(self) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            assert check_contract_version(__contract_version__) is None

    def test_patch_only_mismatch_is_noop(self) -> None:
        major, minor, _patch = __contract_version__.split(".")
        bumped_patch = f"{major}.{minor}.99"
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            assert check_contract_version(bumped_patch) is None

    def test_minor_mismatch_emits_user_warning(self) -> None:
        """On ≥1.0, minor-mismatch warns. On 0.x, minor-mismatch hard-fails."""
        major, minor, patch = __contract_version__.split(".")
        bumped_minor = f"{major}.{int(minor) + 1}.{patch}"
        if int(major) == 0:
            with pytest.raises(ContractError):
                check_contract_version(bumped_minor)
        else:
            with pytest.warns(UserWarning):
                check_contract_version(bumped_minor)

    def test_minor_mismatch_downgrade_also_warns(self) -> None:
        """On ≥1.0, minor-downgrade warns. On 0.x, it hard-fails."""
        major, minor, patch = __contract_version__.split(".")
        if int(minor) == 0:
            pytest.skip("cannot downgrade minor below 0")
        lower_minor = f"{major}.{int(minor) - 1}.{patch}"
        if int(major) == 0:
            with pytest.raises(ContractError):
                check_contract_version(lower_minor)
        else:
            with pytest.warns(UserWarning):
                check_contract_version(lower_minor)

    def test_minor_mismatch_on_zerox_hard_fails(self) -> None:
        """Explicit coverage: pre-1.0 minor mismatch is a contract break."""
        from halcytone_contracts.drift import _parse_semver

        major, _, _ = _parse_semver(__contract_version__)
        if major != 0:
            pytest.skip("only applies while package is in 0.x")
        _, minor, patch = __contract_version__.split(".")
        bumped = f"0.{int(minor) + 1}.{patch}"
        with pytest.raises(ContractError) as exc_info:
            check_contract_version(bumped)
        assert "pre-1.0" in str(exc_info.value)

    def test_major_mismatch_raises(self) -> None:
        major, minor, patch = __contract_version__.split(".")
        bumped_major = f"{int(major) + 1}.{minor}.{patch}"
        with pytest.raises(ContractError):
            check_contract_version(bumped_major)

    def test_major_downgrade_raises(self) -> None:
        major, minor, patch = __contract_version__.split(".")
        if int(major) == 0:
            with pytest.raises(ContractError):
                check_contract_version(f"1.{minor}.{patch}")
        else:
            with pytest.raises(ContractError):
                check_contract_version(f"{int(major) - 1}.{minor}.{patch}")

    def test_malformed_version_raises_contract_error(self) -> None:
        with pytest.raises(ContractError):
            check_contract_version("not-a-version")

    def test_two_segment_version_raises_contract_error(self) -> None:
        with pytest.raises(ContractError):
            check_contract_version("1.0")

    def test_empty_string_raises_contract_error(self) -> None:
        with pytest.raises(ContractError):
            check_contract_version("")

    def test_returns_none_on_success(self) -> None:
        assert check_contract_version(__contract_version__) is None
