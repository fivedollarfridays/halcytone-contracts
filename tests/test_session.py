"""Tests for halcytone_contracts.session."""

from __future__ import annotations

import re
from datetime import datetime

import pytest
from pydantic import ValidationError

from halcytone_contracts.session import (
    SESSION_ID_REGEX,
    Annotation,
    MapperConfigUpdate,
    SessionStart,
    SessionStop,
    format_session_id,
    new_session_id,
    parse_session_id,
)

_EXAMPLE_DT = datetime(2026, 4, 17, 14, 30, 22)
_EXAMPLE_SLUG = "k7m2"
_EXAMPLE_ID = "20260417-143022-k7m2"


# ---------------------------------------------------------------------------
# SESSION_ID_REGEX
# ---------------------------------------------------------------------------


def test_session_id_regex_is_compiled_pattern() -> None:
    assert isinstance(SESSION_ID_REGEX, re.Pattern)


def test_session_id_regex_matches_readme_example() -> None:
    assert SESSION_ID_REGEX.fullmatch(_EXAMPLE_ID) is not None


@pytest.mark.parametrize(
    "good",
    [
        "20260417-143022-k7m2",
        "20000101-000000-0000",
        "20991231-235959-zzzz",
        "20240229-120000-9z0a",
    ],
)
def test_session_id_regex_accepts_well_formed(good: str) -> None:
    assert SESSION_ID_REGEX.fullmatch(good) is not None


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "20260417-143022",                 # missing slug
        "20260417-143022-k7m2-extra",      # extra segment
        "2026041-143022-k7m2",             # short date
        "202604170-143022-k7m2",           # long date
        "20260417-14322-k7m2",             # short time
        "20260417-1430220-k7m2",           # long time
        "20260417-143022-k7m",             # short slug
        "20260417-143022-k7m2a",           # long slug
        "20260417-143022-K7M2",            # uppercase slug
        "20260417-143022-k7_2",            # slug with underscore
        "20260417-143022-k7-2",            # slug with dash
        "abcdefgh-143022-k7m2",            # non-numeric date
        "20260417-abcdef-k7m2",            # non-numeric time
        " 20260417-143022-k7m2",           # leading whitespace
        "20260417-143022-k7m2 ",           # trailing whitespace
    ],
)
def test_session_id_regex_rejects_malformed(bad: str) -> None:
    assert SESSION_ID_REGEX.fullmatch(bad) is None


# ---------------------------------------------------------------------------
# format_session_id
# ---------------------------------------------------------------------------


def test_format_session_id_shape_matches_readme() -> None:
    assert format_session_id(_EXAMPLE_DT, _EXAMPLE_SLUG) == _EXAMPLE_ID


def test_format_session_id_zero_pads_date_and_time() -> None:
    dt = datetime(2026, 1, 2, 3, 4, 5)
    assert format_session_id(dt, "abcd") == "20260102-030405-abcd"


def test_format_session_id_output_matches_regex() -> None:
    out = format_session_id(_EXAMPLE_DT, _EXAMPLE_SLUG)
    assert SESSION_ID_REGEX.fullmatch(out) is not None


@pytest.mark.parametrize(
    "bad_slug",
    ["", "k7m", "k7m2a", "K7M2", "k_m2", "k-m2", "  aa", "k7m!"],
)
def test_format_session_id_rejects_bad_slug(bad_slug: str) -> None:
    with pytest.raises(ValueError):
        format_session_id(_EXAMPLE_DT, bad_slug)


# ---------------------------------------------------------------------------
# parse_session_id
# ---------------------------------------------------------------------------


def test_parse_session_id_returns_dt_and_slug() -> None:
    dt, slug = parse_session_id(_EXAMPLE_ID)
    assert dt == _EXAMPLE_DT
    assert slug == _EXAMPLE_SLUG


@pytest.mark.parametrize(
    "dt,slug",
    [
        (datetime(2026, 1, 1, 0, 0, 0), "abcd"),
        (datetime(2026, 12, 31, 23, 59, 59), "0000"),
        (datetime(2024, 2, 29, 12, 34, 56), "9z0a"),
        (datetime(2030, 6, 15, 8, 5, 0), "1a2b"),
    ],
)
def test_parse_is_inverse_of_format(dt: datetime, slug: str) -> None:
    assert parse_session_id(format_session_id(dt, slug)) == (dt, slug)


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "20260417-143022",                 # wrong segment count (too few)
        "20260417-143022-k7m2-extra",      # wrong segment count (too many)
        "2026041-143022-k7m2",             # short date
        "20260417-14302-k7m2",             # short time
        "20260417-143022-k7m",             # short slug
        "20260417-143022-k7m2a",           # long slug
        "20260417-143022-K7M2",            # uppercase slug
        "abcdefgh-143022-k7m2",            # non-numeric date
        "20260417-abcdef-k7m2",            # non-numeric time
        "20261301-143022-k7m2",            # month 13 (invalid calendar)
        "20260417-256022-k7m2",            # hour 25 (invalid clock)
    ],
)
def test_parse_session_id_raises_on_malformed(bad: str) -> None:
    with pytest.raises(ValueError):
        parse_session_id(bad)


# ---------------------------------------------------------------------------
# new_session_id
# ---------------------------------------------------------------------------


def test_new_session_id_matches_regex() -> None:
    assert SESSION_ID_REGEX.fullmatch(new_session_id()) is not None


def test_new_session_id_is_parseable() -> None:
    sid = new_session_id()
    dt, slug = parse_session_id(sid)
    assert isinstance(dt, datetime)
    assert len(slug) == 4


def test_new_session_id_1000_unique() -> None:
    ids = {new_session_id() for _ in range(1000)}
    assert len(ids) == 1000


# ---------------------------------------------------------------------------
# SessionStart
# ---------------------------------------------------------------------------


def test_session_start_ok() -> None:
    s = SessionStart(session_id=_EXAMPLE_ID, config={"baseline_s": 60})
    assert s.session_id == _EXAMPLE_ID
    assert s.config == {"baseline_s": 60}


def test_session_start_requires_session_id() -> None:
    with pytest.raises(ValidationError):
        SessionStart(config={})  # type: ignore[call-arg]


def test_session_start_requires_config() -> None:
    with pytest.raises(ValidationError):
        SessionStart(session_id=_EXAMPLE_ID)  # type: ignore[call-arg]


def test_session_start_rejects_invalid_session_id() -> None:
    with pytest.raises(ValidationError):
        SessionStart(session_id="not-an-id", config={})


def test_session_start_forbids_extra() -> None:
    with pytest.raises(ValidationError):
        SessionStart(session_id=_EXAMPLE_ID, config={}, extra="nope")  # type: ignore[call-arg]


def test_session_start_json_roundtrip() -> None:
    s = SessionStart(session_id=_EXAMPLE_ID, config={"k": 1, "nested": {"a": [1, 2]}})
    s2 = SessionStart.model_validate_json(s.model_dump_json())
    assert s2 == s


# ---------------------------------------------------------------------------
# SessionStop
# ---------------------------------------------------------------------------


def test_session_stop_is_empty_model() -> None:
    assert SessionStop().model_dump() == {}


def test_session_stop_forbids_extra() -> None:
    with pytest.raises(ValidationError):
        SessionStop(whatever=1)  # type: ignore[call-arg]


def test_session_stop_json_roundtrip() -> None:
    assert SessionStop.model_validate_json(SessionStop().model_dump_json()) == SessionStop()


# ---------------------------------------------------------------------------
# Annotation
# ---------------------------------------------------------------------------


def test_annotation_ok() -> None:
    a = Annotation(t_ns=1_700_000_000_000_000_000, label="deep-breath", data={"by": "user"})
    assert a.t_ns == 1_700_000_000_000_000_000
    assert a.label == "deep-breath"
    assert a.data == {"by": "user"}


def test_annotation_requires_all_fields() -> None:
    with pytest.raises(ValidationError):
        Annotation(t_ns=1, label="tag")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        Annotation(t_ns=1, data={})  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        Annotation(label="tag", data={})  # type: ignore[call-arg]


def test_annotation_forbids_extra() -> None:
    with pytest.raises(ValidationError):
        Annotation(t_ns=1, label="tag", data={}, extra="nope")  # type: ignore[call-arg]


def test_annotation_json_roundtrip() -> None:
    a = Annotation(t_ns=42, label="x", data={"y": [1, 2]})
    a2 = Annotation.model_validate_json(a.model_dump_json())
    assert a2 == a


# ---------------------------------------------------------------------------
# MapperConfigUpdate
# ---------------------------------------------------------------------------


def test_mapper_config_update_ok() -> None:
    m = MapperConfigUpdate(params={"gain": 1.5, "pitch": "alpha_power"})
    assert m.params == {"gain": 1.5, "pitch": "alpha_power"}


def test_mapper_config_update_requires_params() -> None:
    with pytest.raises(ValidationError):
        MapperConfigUpdate()  # type: ignore[call-arg]


def test_mapper_config_update_forbids_extra() -> None:
    with pytest.raises(ValidationError):
        MapperConfigUpdate(params={}, extra="nope")  # type: ignore[call-arg]


def test_mapper_config_update_json_roundtrip() -> None:
    m = MapperConfigUpdate(params={"gain": 2.0, "nested": {"k": [1, 2, 3]}})
    m2 = MapperConfigUpdate.model_validate_json(m.model_dump_json())
    assert m2 == m
