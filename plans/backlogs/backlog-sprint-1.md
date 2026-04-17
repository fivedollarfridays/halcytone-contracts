# Sprint 1 Backlog — halcytone-contracts v0.1.0 MVP

## Overview

Ship `halcytone-contracts` v0.1.0: a pip-installable Python package (`halcytone_contracts`) containing every schema, type, and protocol spec the seven-repo halcytone fleet depends on. Pydantic v2 for authorship, JSON Schema exported for the cross-language (TypeScript AgentGrounds) manifest boundary, raw SQL DDL that downstream repos wrap themselves, a reserved-stream registry with sample rates and channel counts, drift guardrails (`__contract_version__`, `REQUIRED_SCHEMA_VERSION`, `validate_stream_roster`), and a documented semver policy.

**Scope boundaries:** contracts only — no fusion logic, no I/O, no LSL wrappers, no CLI. If a downstream repo would own it, it stays out of this sprint.

**Stack:** Python 3.11+, pydantic v2, pyyaml, pytest, ruff. Greenfield (0 source files, 1 README, paircoder scaffolding present).

## Phase 1: Scaffold (Wave 0)

### T1.1 — Package scaffold + pyproject | Cx: 2 | P0

**Description:** Stand up the `halcytone_contracts` Python package: `pyproject.toml`, a stub top-level `__init__.py` (version string only — exports are aggregated later in T1.7), test harness, ruff config, and `.gitignore` updates. Runtime deps: pydantic v2, pyyaml. Dev extras: pytest, ruff. Pin Python ≥3.11. This is the foundation all other tasks depend on; keep it minimal and greenfield-clean.

**AC:**
- [ ] `pip install -e .[dev]` succeeds from a clean venv
- [ ] `pytest` runs (zero tests, zero failures, exit 0)
- [ ] `ruff check .` reports clean
- [ ] Python ≥3.11 pin declared in `pyproject.toml`
- [ ] `pydantic` v2 and `pyyaml` declared in runtime dependencies
- [ ] `pytest` and `ruff` declared in `[project.optional-dependencies].dev`
- [ ] `halcytone_contracts/__init__.py` contains a version string only (no forward exports yet — those land in T1.7)
- [ ] `tests/__init__.py` and `tests/conftest.py` exist
- [ ] `.gitignore` updated for Python artifacts (`__pycache__/`, `*.egg-info/`, `.pytest_cache/`, `dist/`, `build/`)
- [ ] Ruff config lives in `[tool.ruff]` inside `pyproject.toml` OR a standalone `ruff.toml`

**Depends on:** none

---

## Phase 2: Core Schemas (Wave 1, parallel)

### T1.2 — signals.py (SignalPacket + StreamSpec + RESERVED_STREAMS) | Cx: 6 | P0

**Description:** Author the signal-layer contracts: a `SignalPacket` pydantic v2 model (the wire shape any sensor emits), a `StreamSpec` frozen dataclass (the registry entry describing a named stream), and the `RESERVED_STREAMS` dict covering every reserved stream name called out in the README (EEG channels + band powers, PPG, HRV, EDA, skin temp, IMU, breath acoustic/envelope/derived). Registry invariants (unique names, positive sample rates, correct `derived` flags) are locked down by tests. No I/O, no LSL — this is pure schema.

**AC:**
- [ ] `SignalPacket` pydantic v2 model with fields `sensor_id`, `stream`, `t_ns`, `values`, `quality`
- [ ] `quality` validated to lie in `[0.0, 1.0]`; out-of-range raises `ValidationError`
- [ ] `StreamSpec` is a frozen dataclass with fields `name`, `domain`, `sample_rate_hz`, `channel_count`, `dtype`, `derived`, `archive_only`
- [ ] `RESERVED_STREAMS: dict[str, StreamSpec]` covers every reserved name in the README (`eeg.ch1`–`eeg.ch4`, EEG band powers, `ppg`, `hrv.rmssd`, `hrv.sdnn`, `eda`, `skin_temp`, `imu.accel`, `imu.gyro`, `breath.acoustic`, `breath.envelope`, `breath.rate`, `breath.phase`, `breath.depth`)
- [ ] Test: no duplicate names in `RESERVED_STREAMS`
- [ ] Test: every `sample_rate_hz > 0` and every `channel_count >= 1`
- [ ] Test: derived streams flagged correctly — e.g., `eeg.alpha.derived == True`, `eeg.ch1.derived == False`
- [ ] Test: round-trip JSON serialize/deserialize of a `SignalPacket` preserves all fields
- [ ] `bpsai-pair arch check halcytone_contracts/signals.py` clean

**Depends on:** T1.1

---

### T1.3 — state.py (StateVector) | Cx: 4 | P0

**Description:** Author the fused `StateVector` pydantic v2 model — the per-tick output of the downstream fusion layer, logged one-per-line to `state.jsonl`. Flat struct by design (no nested models), matching the README's "flat struct by choice" note. Normalize numeric ranges via pydantic validators so downstream consumers can trust bounds without re-checking.

**AC:**
- [ ] Every field from the README's `StateVector` spec present with the correct type
- [ ] `breath_phase` validated in `[0, 1]`
- [ ] `breath_depth` validated in `[0, 1]`
- [ ] `heart_breath_coherence` validated in `[0, 1]`
- [ ] `overall_presence` validated in `[0, 1]`
- [ ] All `eeg_*` normalized fields validated in `[0, 1]`
- [ ] Model is a flat struct — no nested pydantic sub-models
- [ ] Test: round-trip JSON serialize/deserialize preserves all fields
- [ ] Test: JSONL-line serialization — `model_dump_json()` output fits one line and parses back via `StateVector.model_validate_json()`
- [ ] `bpsai-pair arch check halcytone_contracts/state.py` clean

**Depends on:** T1.1

---

### T1.4 — session.py (control messages + session_id) | Cx: 4 | P1

**Description:** Author the session-control contracts: pydantic v2 models for `SessionStart`, `SessionStop`, `Annotation`, `MapperConfigUpdate` (the models flow on the runtime bus — the bus itself lives in halcytone-core). Plus the canonical session-id format and helpers. The session-id regex becomes the single source of truth consumed by the manifest in T1.6.

**AC:**
- [ ] `SessionStart`, `SessionStop`, `Annotation`, `MapperConfigUpdate` pydantic v2 models defined
- [ ] `format_session_id(dt, slug) -> str` helper produces `{YYYYMMDD}-{HHMMSS}-{slug4}` format
- [ ] `parse_session_id(s) -> tuple` helper returns `(datetime, slug)` and is the inverse of `format_session_id`
- [ ] Session-ID regex exported as a module-level constant and matches the README format exactly
- [ ] `new_session_id() -> str` generates valid IDs that pass the regex
- [ ] Test: `parse_session_id(format_session_id(dt, slug)) == (dt, slug)` for representative inputs
- [ ] Test: 1000 sequential `new_session_id()` calls yield 1000 unique IDs
- [ ] Test: malformed session IDs (wrong segment count, bad slug length, non-numeric date/time) raise on `parse_session_id`
- [ ] `bpsai-pair arch check halcytone_contracts/session.py` clean

**Depends on:** T1.1

---

### T1.5 — storage.sql + storage.py loader | Cx: 5 | P0

**Description:** Define the raw SQL DDL that every downstream repo wraps — no ORM, no SQLAlchemy layer. Tables: `sessions`, `baselines`, `annotations`, `state_summaries`, plus a `meta` table seeded with `schema_version`. `storage.py` exposes `SCHEMA_VERSION: int` (matching the seeded row) and `read_ddl() -> str` so consumers can apply the DDL at setup. Idempotent via `CREATE TABLE IF NOT EXISTS`.

**AC:**
- [ ] `halcytone_contracts/storage.sql` defines tables: `sessions`, `baselines`, `annotations`, `state_summaries`, `meta`
- [ ] `meta` table seeded with a `schema_version` row at DDL apply time
- [ ] `SCHEMA_VERSION: int` constant defined in `storage.py` and equals the value seeded in `meta`
- [ ] `read_ddl() -> str` returns the full DDL as a string (reads the packaged `.sql` via importlib.resources)
- [ ] Test: open in-memory sqlite, execute `read_ddl()`, assert each expected table exists via `PRAGMA table_info`
- [ ] Test: DDL is idempotent — executing it twice against the same in-memory database raises no error (all statements use `CREATE TABLE IF NOT EXISTS` or equivalent)
- [ ] Test: after DDL apply, `SELECT value FROM meta WHERE key='schema_version'` returns `str(SCHEMA_VERSION)`
- [ ] `bpsai-pair arch check halcytone_contracts/storage.py` clean

**Depends on:** T1.1

---

## Phase 3: Manifest + Drift Guardrails (Wave 2)

### T1.6 — bundles/manifest.py + generated manifest.schema.json | Cx: 6 | P1

**Description:** Build the session-bundle manifest — the cross-language boundary artifact consumed by the TypeScript AgentGrounds side. `SessionManifest` pydantic v2 model covers every field from the README manifest. A regen script emits `manifest.schema.json` via `model_json_schema()`, and that generated file is checked in. A byte-equality test compares fresh regen output against the checked-in file, giving CI a drift detector for free.

**AC:**
- [ ] `halcytone_contracts/bundles/__init__.py` exists
- [ ] `SessionManifest` pydantic v2 model with fields: `session_id`, `started_at`, `ended_at`, `duration_s`, `sensors`, `baselines`, `summary`, `artifacts` (matching README)
- [ ] `session_id` field validated via T1.4's regex (invalid IDs raise `ValidationError`)
- [ ] `ended_at` is `Optional[datetime]`; presence marks session completion (matches README semantic)
- [ ] `scripts/regen_manifest_schema.py` emits `halcytone_contracts/bundles/manifest.schema.json` via `SessionManifest.model_json_schema()`
- [ ] `manifest.schema.json` checked into the repo
- [ ] Test: round-trip yaml → `SessionManifest` → yaml preserves all structural fields
- [ ] Test: running `scripts/regen_manifest_schema.py` produces output byte-equal to the checked-in `manifest.schema.json` (CI drift check)
- [ ] Test: `ended_at=None` accepted (in-progress session); populated `ended_at` accepted (completed session)
- [ ] `bpsai-pair arch check halcytone_contracts/bundles/manifest.py` clean

**Depends on:** T1.4

---

### T1.7 — Drift helpers + top-level exports | Cx: 3 | P1

**Description:** Wire the public surface area. Expand `halcytone_contracts/__init__.py` to re-export everything the fleet will import. Add `__contract_version__` (string, must match `pyproject.toml` version) and re-export `SCHEMA_VERSION` from storage as `REQUIRED_SCHEMA_VERSION`. Add two drift helpers: `validate_stream_roster` (verifies a published set covers required streams, raises `ContractError` with a diff on mismatch) and `check_contract_version` (hard-fails on major-version mismatch, warns on minor-version mismatch — per prior decision).

**AC:**
- [ ] `__contract_version__: str` defined in `__init__.py` and equals the version in `pyproject.toml`
- [ ] Test: `__contract_version__` matches `pyproject.toml` version string (parse pyproject at test time)
- [ ] `REQUIRED_SCHEMA_VERSION: int` exported from `storage.py` and re-exported at top level (equals `SCHEMA_VERSION`)
- [ ] `validate_stream_roster(published: Iterable[str], required: Iterable[str]) -> None` raises `ContractError` with a diff (what's missing) when `published ⊉ required`; returns `None` when `published ⊇ required`
- [ ] `check_contract_version(consumer_version: str) -> None`: raises `ContractError` on major-version mismatch; emits `warnings.warn` on minor-version mismatch; no-op on exact or patch-only mismatch
- [ ] `ContractError` exception class defined (sensible base — e.g., `RuntimeError` subclass)
- [ ] `__init__.py` exports (at minimum): `SignalPacket`, `StreamSpec`, `RESERVED_STREAMS`, `StateVector`, `SessionStart`, `SessionStop`, `Annotation`, `MapperConfigUpdate`, `SessionManifest`, `SCHEMA_VERSION`, `REQUIRED_SCHEMA_VERSION`, `__contract_version__`, `validate_stream_roster`, `check_contract_version`, `ContractError`
- [ ] Test: `check_contract_version` on a major-mismatch input raises `ContractError`
- [ ] Test: `check_contract_version` on a minor-mismatch input emits a `UserWarning` (asserted via `pytest.warns`)
- [ ] Test: `check_contract_version` on a matching version is a no-op (no raise, no warn)
- [ ] Test: `validate_stream_roster` passes when `published ⊇ required`
- [ ] Test: `validate_stream_roster` raises `ContractError` on missing stream, and the message names the missing stream(s)
- [ ] `bpsai-pair arch check` clean on all modified modules

**Depends on:** T1.2, T1.3, T1.4, T1.5

---

## Phase 4: Docs + Versioning (Wave 3)

### T1.8 — ROADMAP, CHANGELOG, versioning docs | Cx: 2 | P1

**Description:** Lock the semver story downstream repos will pin against. Add `ROADMAP.md` with v0.1.0 / v0.1.x / v0.2.0 / v0.3.0 milestones, seed `CHANGELOG.md` at 0.1.0 with a populated "Added" section, and append a "Versioning" section to `README.md` documenting the pin pattern (`halcytone-contracts>=0.1,<0.2`) and the `__contract_version__` runtime check pattern. Reconcile the README's "Open design questions" section.

**AC:**
- [ ] `ROADMAP.md` created at repo root with milestones for v0.1.0, v0.1.x (patch band), v0.2.0, v0.3.0 — each with a short scope statement
- [ ] `CHANGELOG.md` created at repo root following Keep-a-Changelog format, with a `## [0.1.0]` section containing a populated "Added" list that names the modules shipped this sprint
- [ ] `README.md` gains a "Versioning" section covering: semver policy (major = breaking contract change, minor = additive, patch = fixes), the downstream pin recommendation `halcytone-contracts>=0.1,<0.2`, and a runtime check example using `check_contract_version`
- [ ] `README.md` "Open design questions" section reconciled — drop the "None open" placeholder, link to `ROADMAP.md` for forward-looking items
- [ ] Links in the new README section resolve to files that exist in the repo

**Depends on:** T1.7

---

## Delivery Summary

| Task | Title | Cx | Pri | Depends |
|------|-------|----|-----|---------|
| T1.1 | Package scaffold + pyproject | 2 | P0 | — |
| T1.2 | signals.py (SignalPacket + StreamSpec + RESERVED_STREAMS) | 6 | P0 | T1.1 |
| T1.3 | state.py (StateVector) | 4 | P0 | T1.1 |
| T1.4 | session.py (control messages + session_id) | 4 | P1 | T1.1 |
| T1.5 | storage.sql + storage.py loader | 5 | P0 | T1.1 |
| T1.6 | bundles/manifest.py + generated manifest.schema.json | 6 | P1 | T1.4 |
| T1.7 | Drift helpers + top-level exports | 3 | P1 | T1.2, T1.3, T1.4, T1.5 |
| T1.8 | ROADMAP, CHANGELOG, versioning docs | 2 | P1 | T1.7 |

**Sprint Budget:** 32 Cx across 8 tasks — P0 ×4, P1 ×4, P2 ×0.

**Cut order if budget overflows:** T1.8 → T1.6 → T1.7 → T1.4. Cutting any P0 fails the sprint.

## Priority Order

1. **T1.1** — scaffold (P0, blocks everything)
2. **T1.2** — signals (P0, wave 1, parallel)
3. **T1.3** — state (P0, wave 1, parallel)
4. **T1.5** — storage (P0, wave 1, parallel)
5. **T1.4** — session (P1, wave 1, parallel — needed by T1.6)
6. **T1.6** — manifest (P1, wave 2)
7. **T1.7** — drift helpers + exports (P1, wave 2)
8. **T1.8** — roadmap/changelog/versioning docs (P1, wave 3)

## Dependency Graph

```
Wave 0:  T1.1
           ↓
Wave 1:  T1.2   T1.3   T1.4   T1.5      (parallel — no file overlap)
                        ↓       ↓
Wave 2:                T1.6    T1.7 (← T1.2, T1.3, T1.4, T1.5)
                                ↓
Wave 3:                        T1.8
```

## Integration Points

- **T1.2 → T1.7:** `RESERVED_STREAMS` registry feeds `validate_stream_roster`.
- **T1.4 → T1.6:** session-id regex is the single source; manifest validates `session_id` against it.
- **T1.5 → T1.7:** `SCHEMA_VERSION` constant is re-exported as `REQUIRED_SCHEMA_VERSION`.
- **T1.6 → CI (future):** `manifest.schema.json` regen diff check.
- **All wave-1 modules → T1.7:** top-level `__init__.py` exports.

## Out of Scope

- LSL wire-protocol wrappers, pylsl integration (lives in halcytone-sensors / halcytone-core)
- SQLAlchemy / ORM layer — each repo wraps raw DDL
- halcytone-publish ffmpeg composition logic
- Paircoder template for sibling halcytone-* repos (deferred to v0.2.0 per roadmap)
- Runtime asyncio bus for SessionStart/SessionStop — models only; bus lives in halcytone-core
- PyPI publishing — v0.1.0 ships as a git dep; PyPI is post-MVP
- Baseline format specification beyond `manifest.baselines: dict` — detailed baseline schema is v0.3.0
