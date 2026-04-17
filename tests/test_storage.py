"""Tests for halcytone_contracts.storage — raw SQL DDL + loader."""

from __future__ import annotations

import sqlite3
from importlib import resources

import pytest

from halcytone_contracts import storage

EXPECTED_TABLES = {"sessions", "baselines", "annotations", "state_summaries", "meta"}


def _table_names(conn: sqlite3.Connection) -> set[str]:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return {row[0] for row in cur.fetchall()}


def _apply_ddl(conn: sqlite3.Connection) -> None:
    conn.executescript(storage.read_ddl())


# ---------------------------------------------------------------------------
# read_ddl()
# ---------------------------------------------------------------------------


def test_read_ddl_returns_str():
    ddl = storage.read_ddl()
    assert isinstance(ddl, str)
    assert ddl.strip(), "read_ddl() returned empty string"


def test_read_ddl_is_cacheable_pure_function():
    assert storage.read_ddl() == storage.read_ddl()


def test_read_ddl_uses_importlib_resources():
    pkg_text = resources.files("halcytone_contracts").joinpath("storage.sql").read_text(
        encoding="utf-8"
    )
    assert storage.read_ddl() == pkg_text


def test_read_ddl_mentions_each_expected_table():
    ddl = storage.read_ddl()
    for tbl in EXPECTED_TABLES:
        assert tbl in ddl, f"DDL does not mention table {tbl!r}"


def test_read_ddl_uses_create_table_if_not_exists_for_every_table():
    ddl = storage.read_ddl().lower()
    assert ddl.count("create table if not exists") >= len(EXPECTED_TABLES)
    assert "create table " in ddl
    non_idempotent = [
        line
        for line in ddl.splitlines()
        if line.strip().startswith("create table ")
        and "if not exists" not in line
    ]
    assert non_idempotent == [], (
        f"Non-idempotent CREATE TABLE statements found: {non_idempotent}"
    )


# ---------------------------------------------------------------------------
# SCHEMA_VERSION
# ---------------------------------------------------------------------------


def test_schema_version_is_int():
    assert isinstance(storage.SCHEMA_VERSION, int)
    assert storage.SCHEMA_VERSION >= 1


# ---------------------------------------------------------------------------
# DDL apply — sqlite :memory:
# ---------------------------------------------------------------------------


def test_apply_creates_every_expected_table():
    conn = sqlite3.connect(":memory:")
    try:
        _apply_ddl(conn)
        assert EXPECTED_TABLES.issubset(_table_names(conn))
    finally:
        conn.close()


@pytest.mark.parametrize("table", sorted(EXPECTED_TABLES))
def test_pragma_table_info_non_empty_for_each_table(table: str):
    conn = sqlite3.connect(":memory:")
    try:
        _apply_ddl(conn)
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        assert rows, f"PRAGMA table_info({table}) returned no rows"
    finally:
        conn.close()


def test_meta_seeded_with_schema_version():
    conn = sqlite3.connect(":memory:")
    try:
        _apply_ddl(conn)
        row = conn.execute(
            "SELECT value FROM meta WHERE key='schema_version'"
        ).fetchone()
        assert row is not None, "meta table missing schema_version row"
        assert row[0] == str(storage.SCHEMA_VERSION)
    finally:
        conn.close()


def test_ddl_is_idempotent_applied_twice():
    conn = sqlite3.connect(":memory:")
    try:
        _apply_ddl(conn)
        _apply_ddl(conn)  # must not raise
        assert EXPECTED_TABLES.issubset(_table_names(conn))
        rows = conn.execute(
            "SELECT value FROM meta WHERE key='schema_version'"
        ).fetchall()
        assert len(rows) == 1, f"schema_version row duplicated after re-apply: {rows}"
        assert rows[0][0] == str(storage.SCHEMA_VERSION)
    finally:
        conn.close()


def test_sessions_table_has_session_id_column():
    conn = sqlite3.connect(":memory:")
    try:
        _apply_ddl(conn)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(sessions)").fetchall()}
        assert "session_id" in cols
    finally:
        conn.close()


def test_annotations_table_has_t_ns_and_label_columns():
    conn = sqlite3.connect(":memory:")
    try:
        _apply_ddl(conn)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(annotations)").fetchall()}
        assert "t_ns" in cols
        assert "label" in cols
    finally:
        conn.close()


def test_meta_table_is_key_value_shape():
    conn = sqlite3.connect(":memory:")
    try:
        _apply_ddl(conn)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(meta)").fetchall()}
        assert {"key", "value"}.issubset(cols)
    finally:
        conn.close()
