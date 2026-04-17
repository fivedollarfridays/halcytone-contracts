-- halcytone-contracts storage DDL
-- Raw SQL contract for the on-disk SQLite at ~/halcytone/halcytone.db.
-- Every downstream repo wraps this DDL directly — no ORM layer.
-- All CREATE TABLE statements are idempotent (IF NOT EXISTS).

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id  TEXT PRIMARY KEY,
    started_at  TEXT NOT NULL,
    ended_at    TEXT,
    duration_s  REAL,
    config_json TEXT
);

CREATE TABLE IF NOT EXISTS baselines (
    session_id TEXT NOT NULL,
    metric     TEXT NOT NULL,
    value      REAL NOT NULL,
    PRIMARY KEY (session_id, metric),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS annotations (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    t_ns       INTEGER NOT NULL,
    label      TEXT NOT NULL,
    data_json  TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE TABLE IF NOT EXISTS state_summaries (
    session_id TEXT NOT NULL,
    metric     TEXT NOT NULL,
    value      REAL NOT NULL,
    PRIMARY KEY (session_id, metric),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- Seed the schema_version row. INSERT OR IGNORE keeps the DDL idempotent:
-- re-applying never duplicates or overwrites the row.
INSERT OR IGNORE INTO meta (key, value) VALUES ('schema_version', '1');
