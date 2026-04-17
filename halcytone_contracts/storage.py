"""Raw SQL storage contract: DDL loader + schema version constant.

Downstream repos (halcytone-core is the primary consumer) wrap the DDL in
their own connection / migration layer — this package stays ORM-free and
I/O-free. `read_ddl()` hands back the packaged ``storage.sql`` as text so
consumers can `executescript` it against any sqlite3 connection.

`SCHEMA_VERSION` is the single source of truth: it matches the value seeded
into the ``meta`` table at DDL apply time, so consumers can cross-check a
live database against the contract they pinned against.
"""

from __future__ import annotations

from importlib import resources

SCHEMA_VERSION: int = 1

_DDL_RESOURCE = "storage.sql"


def read_ddl() -> str:
    """Return the packaged ``storage.sql`` DDL as a UTF-8 string."""
    return (
        resources.files("halcytone_contracts")
        .joinpath(_DDL_RESOURCE)
        .read_text(encoding="utf-8")
    )


__all__ = ["SCHEMA_VERSION", "read_ddl"]
