# Current State

> Last updated: 2026-04-17

## Active Plan

**Plan:** `plan-2026-04-sprint-1-v0-1-0-mvp` — Sprint 1 — halcytone-contracts v0.1.0 MVP
**Status:** Planned (Navigator handoff complete; ready for Driver)
**Current Sprint:** sprint-1
**Total Cx:** 32 across 8 tasks (P0 ×4 · P1 ×4)
**Source backlog:** `plans/backlogs/backlog-sprint-1.md`

## Current Focus

Ship `halcytone-contracts` v0.1.0: a pip-installable Python package containing every schema, type, and protocol spec the seven-repo halcytone fleet depends on. Pydantic v2 for authorship, JSON Schema exported for cross-language boundary, raw SQL DDL, reserved-stream registry, drift guardrails, and a documented semver policy. **Scope boundary:** contracts only — no fusion logic, no I/O, no LSL wrappers, no CLI.

## Task Status

### Active Sprint — sprint-1

| Task | Title | Cx | Pri | Wave | Status | Depends |
|------|-------|----|-----|------|--------|---------|
| T1.1 | Package scaffold + pyproject | 15 | P0 | 0 | ✓ done | — |
| T1.2 | signals.py (SignalPacket + StreamSpec + RESERVED_STREAMS) | 50 | P0 | 1 | ✓ done | T1.1 |
| T1.3 | state.py (StateVector) | 35 | P0 | 1 | ✓ done | T1.1 |
| T1.4 | session.py (control messages + session_id) | 35 | P1 | 1 | ✓ done | T1.1 |
| T1.5 | storage.sql + storage.py loader | 40 | P0 | 1 | ✓ done | T1.1 |
| T1.6 | bundles/manifest.py + generated manifest.schema.json | 50 | P1 | 2 | ✓ done | T1.4 |
| T1.7 | Drift helpers + top-level exports | 25 | P1 | 2 | ✓ done | T1.2, T1.3, T1.4, T1.5 |
| T1.8 | ROADMAP, CHANGELOG, versioning docs | 15 | P1 | 3 | ✓ done | T1.7 |

> Cx totals above use the `plan add-task` 0–100 complexity scale (Cx points × ~8 per unit from the backlog's 32-Cx sprint budget). Backlog Cx columns: T1.1=2, T1.2=6, T1.3=4, T1.4=4, T1.5=5, T1.6=6, T1.7=3, T1.8=2.

### Dependency Graph

```
Wave 0:  T1.1
           ↓
Wave 1:  T1.2   T1.3   T1.4   T1.5      (parallel — no file overlap)
                        ↓       ↓
Wave 2:                T1.6    T1.7 (← T1.2, T1.3, T1.4, T1.5)
                                ↓
Wave 3:                        T1.8
```

### Cut Order if Budget Overflows

`T1.8 → T1.6 → T1.7 → T1.4`. Cutting any P0 (T1.1, T1.2, T1.3, T1.5) fails the sprint.

### Backlog

No deprioritized items. All backlog entries pulled into the active sprint.

## What Was Just Done

### Session: 2026-04-17 — Sprint-1 review + fix + ship (reviewing-and-fixing)

- **Engage misreport:** T1.8 flagged "already satisfied -- skipping" but was actually `pending` with no output. Caught during doc-cleanup inventory, folded into the review-fix pipeline.
- **Code review** (nayru on full `main...HEAD` + CI workflow): 0 Must Fix, 7 Should Fix, 10 Consider. Plus a second pass (parallel reuse/quality/efficiency agents) surfaced the `_Unit` alias miss in `SignalPacket.quality`, the missing session-helper exports, and a 220ms redundant subprocess test.
- **Applied fixes:** extracted `SessionId = Annotated[str, AfterValidator(...)]` in `session.py` (replaces 3× duplicate regex check across SessionStart/StateVector/SessionManifest); shared `Unit` alias from `signals.py` for every `[0,1]` field; bounded `StateVector.breath_quality` / `hrv_quality`; added `min_length=1` on `SignalPacket.sensor_id`/`stream` + `ge=0` on `t_ns`; added `ge=0` to `StateVector.t_ns` and `Annotation.t_ns`; **0.x semver sharpening** in `check_contract_version` — hard-fail on minor mismatch while major==0 (matches `>=0.1,<0.2` pin semantics and semver.org §4); expanded `__init__.py` exports to include `SessionId`, `SESSION_ID_REGEX`, session helpers, `read_ddl`; deleted the redundant subprocess-spawning schema-drift test (in-process `model_json_schema()` comparison covers the same invariant — suite is now 60% faster, 0.49s).
- **T1.8 completed:** wrote `ROADMAP.md` (v0.1.0 / v0.1.x / v0.2.0 / v0.3.0 / v1.0.0 milestones), `CHANGELOG.md` (Keep-a-Changelog seeded at 0.1.0), README Versioning section (semver policy, downstream pin `halcytone-contracts>=0.1,<0.2`, `check_contract_version` runtime pattern, schema-drift detector note). Reconciled the "Open design questions" placeholder.
- **CI landed:** `.github/workflows/ci.yml` with ruff, pytest matrix (3.11/3.12/3.13), and schema-drift jobs. Python 3.13 added to pyproject classifiers.
- **Security audit decoded:** engage's "PR blocked by security audit" was `scan-deps` flagging 16 HIGH CVEs in the shared venv — 15 are env packages this repo never declares (aiohttp, cryptography, pillow, pygments, python-multipart); the one overlap (`pytest 9.0.2 → 9.0.3`) is already satisfied by our `>=7.4` pin. `scan-secrets` clean.
- **Shipped:** commit `853e5b6`, branch `engage/backlog-sprint-1` pushed, PR [#1](https://github.com/fivedollarfridays/halcytone-contracts/pull/1) open. CI: 5/5 jobs green in ~17s.
- Verified locally: **272 pytest passing**, `ruff check .` clean, schema drift clean, secret scan clean.

### Session: 2026-04-17 — T1.7 Drift helpers + top-level exports (Driver)

- TDD: added `tests/test_drift.py` (22 tests) covering `ContractError` inheritance chain, `validate_stream_roster` happy paths (exact / superset / empty required / set / generator inputs) and failure modes (single + multi missing, all-missing, message names only missing streams and *not* extras), and `check_contract_version` across exact match, patch-only, minor bump/downgrade (warns), major bump/downgrade (raises), malformed / two-segment / empty strings (raise), plus no-op return sanity. Added `tests/test_exports.py` (10 tests) parsing `pyproject.toml` with `tomllib` to assert `__contract_version__` equality, `REQUIRED_SCHEMA_VERSION == SCHEMA_VERSION`, full `__all__` coverage of the 15 backlog-required names, and submodule-identity checks (re-exports point to the same objects, not copies).
- Added `halcytone_contracts/drift.py`: `ContractError(RuntimeError)`, `validate_stream_roster(published, required)` (set-difference, sorted missing list in message for deterministic diffs), `check_contract_version(consumer_version)` with lazy `__contract_version__` import (breaks the otherwise-circular load order) and a small `_parse_semver` helper that routes every malformed-string failure through `ContractError`.
- Updated `halcytone_contracts/storage.py` with `REQUIRED_SCHEMA_VERSION: int = SCHEMA_VERSION` alias and appended to `__all__`.
- Rewrote `halcytone_contracts/__init__.py` to re-export the full public surface (`SignalPacket`, `StreamSpec`, `RESERVED_STREAMS`, `StateVector`, 4 session models, `SessionManifest`, `SCHEMA_VERSION`, `REQUIRED_SCHEMA_VERSION`, drift trio) and define `__contract_version__ = "0.1.0"` with `__version__` kept as an in-lockstep alias.
- Verified: `pytest` **250 passed** (32 new + 218 carried), `ruff check .` clean, `bpsai-pair arch check` clean on `drift.py`, `__init__.py`, and `storage.py`. All 12 backlog ACs satisfied.

### Session: 2026-04-17 — T1.6 bundles/manifest.py + manifest.schema.json (Driver)

- TDD: wrote `tests/test_manifest.py` (12 tests) covering complete payload acceptance, invalid `session_id` rejection (via T1.4's `SESSION_ID_REGEX`), `extra="forbid"`, `ended_at` tri-state (None / populated / missing-defaults-to-None), YAML round-trip for both in-progress and completed sessions, checked-in schema presence, `model_json_schema()` parity, subprocess byte-equality against `scripts/regen_manifest_schema.py --stdout` (CI drift guard), and `importlib.resources` verification that the JSON ships inside the installed package.
- Added `halcytone_contracts/bundles/__init__.py` re-exporting `SessionManifest`, and `halcytone_contracts/bundles/manifest.py` with the pydantic v2 model (`session_id`, `started_at`, `ended_at: Optional[datetime] = None`, `duration_s`, `sensors`, `baselines`, `summary`, `artifacts`). `session_id` is regex-validated via `field_validator` importing `SESSION_ID_REGEX` from `halcytone_contracts.session` — T1.4 stays the single source of truth for the format.
- Added `scripts/regen_manifest_schema.py` — argparse CLI with a `--stdout` mode used by the drift test. Canonical rendering is `json.dumps(schema, indent=2, sort_keys=True) + "\n"` so ordering is deterministic across reruns.
- Generated and committed `halcytone_contracts/bundles/manifest.schema.json`. Updated `pyproject.toml` with `"halcytone_contracts.bundles" = ["*.json"]` package-data entry so the schema ships inside the installed wheel/sdist.
- Verified: `pytest` **217 passed** (12 new + 205 carried), `ruff check` clean on changed files, `bpsai-pair arch check halcytone_contracts/bundles/manifest.py` clean (also checked `__init__.py` and the regen script). AC all satisfied.

### Session: 2026-04-17 — T1.5 storage.sql + storage.py loader (Driver)

- TDD: wrote `tests/test_storage.py` (17 tests) covering `read_ddl()` return type + purity, importlib.resources parity with the on-disk `.sql`, presence of each expected table name in the DDL text, idempotency assertion (all `CREATE TABLE` statements use `IF NOT EXISTS` — no non-idempotent variants), `SCHEMA_VERSION` int-ness/positivity, parametrized `PRAGMA table_info` smoke per table, `meta` seed row equals `str(SCHEMA_VERSION)`, re-apply idempotency (second `executescript` raises nothing and schema_version is still a single row), and shape sanity checks on `sessions.session_id`, `annotations.{t_ns,label}`, and `meta.{key,value}`.
- Added `halcytone_contracts/storage.sql`: raw DDL for `meta`, `sessions`, `baselines`, `annotations`, `state_summaries`. Every `CREATE TABLE` uses `IF NOT EXISTS`; the schema_version seed uses `INSERT OR IGNORE` so re-apply never duplicates or overwrites. FK columns reference `sessions(session_id)` where appropriate. No ORM, no migrations framework — downstream repos wrap this directly.
- Added `halcytone_contracts/storage.py`: `SCHEMA_VERSION: int = 1` matching the seeded row, and `read_ddl() -> str` reading the packaged `.sql` via `importlib.resources.files("halcytone_contracts").joinpath("storage.sql").read_text(...)`. Module is 28 lines, one public function — well under arch-check thresholds.
- Updated `pyproject.toml` with `[tool.setuptools.package-data] halcytone_contracts = ["*.sql"]` so the DDL ships inside the installed wheel/sdist (importlib.resources would otherwise miss the non-`.py` file post-install).
- Verified: `pytest` **205 passed** (17 new + 188 carried), `ruff check .` clean, `bpsai-pair arch check halcytone_contracts/storage.py` clean, `pip install -e .` round-trip confirms `read_ddl()` returns the packaged `.sql` content after install.

### Session: 2026-04-17 — T1.4 session.py (control messages + session_id) (Driver)

- TDD: wrote `tests/test_session.py` (70 tests) covering `SESSION_ID_REGEX` shape (well-formed / malformed parametrized), `format_session_id` zero-padding + slug validation, `parse_session_id` inverse-of-format round-trip + malformed rejection (wrong segment count, bad slug length/case/chars, non-numeric date/time, invalid calendar month / clock hour), `new_session_id` regex compliance + parseability + **1000-unique** stress, and per-model (required fields, extra="forbid", JSON round-trip) coverage for all four control messages.
- Added `halcytone_contracts/session.py`:
  - `SESSION_ID_REGEX = re.compile(r"^\d{8}-\d{6}-[0-9a-z]{4}$")` exported as module-level constant (README §"Session protocol" format: `{YYYYMMDD}-{HHMMSS}-{slug4}`).
  - `format_session_id(dt, slug)` uses `dt.strftime("%Y%m%d-%H%M%S")` + slug; slug validated against `[0-9a-z]{4}`.
  - `parse_session_id(s)` regex-guards then `strptime`s — invalid calendar/clock values bubble up as `ValueError`.
  - `new_session_id()` combines UTC naive wall-clock with a thread-safe monotonic counter (random starting offset in `[0, 36**4)`, mod 1_679_616) so 1000 consecutive calls in a tight loop are guaranteed unique.
  - Pydantic v2 models: `SessionStart(session_id, config)` with regex-enforcing `field_validator`, empty `SessionStop()`, `Annotation(t_ns, label, data)`, `MapperConfigUpdate(params)` — all `extra="forbid"` matching sibling contract style.
- Verified: `pytest` **188 passed** (70 new + 118 carried), `ruff check .` clean, `bpsai-pair arch check halcytone_contracts/session.py` clean.

### Session: 2026-04-17 — T1.3 state.py (StateVector) (Driver)

- TDD: wrote `tests/test_state.py` (71 tests) covering field set, flat-struct invariant (no nested pydantic sub-models), field types, extra="forbid" rejection, `[0,1]` bounds on `breath_phase`/`breath_depth`/`heart_breath_coherence`/`overall_presence`/all `eeg_*` normalized fields (incl. inclusive edges 0.0/1.0), JSON round-trip, dict round-trip, JSONL single-line shape, `json.loads` compatibility, multi-record JSONL roundtrip.
- Added `halcytone_contracts/state.py`:
  - `StateVector` pydantic v2 model with every field from README spec (`t_ns`, `session_id`, breath/cardiovascular/autonomic/neural/composite blocks — 19 fields total).
  - `_Unit = Annotated[float, Field(ge=0.0, le=1.0)]` applied to the 10 normalized fields per AC; unbounded `float` for rate/level/ms/µS quantities.
  - `extra="forbid"` to match `SignalPacket` contract style.
- Verified: `pytest` 118 passed (71 new + 47 carried), `ruff check` clean, `bpsai-pair arch check halcytone_contracts/state.py` clean.

### Session: 2026-04-17 — T1.2 signals.py (SignalPacket + StreamSpec + RESERVED_STREAMS) (Driver)

- TDD: wrote `tests/test_signals.py` (47 tests total across suite) covering field set, quality bounds, JSON round-trip, frozen-dataclass invariants, registry coverage/duplicates/rates/channels, derived flags per-stream, archive_only for `breath.acoustic` only, IMU 3-channel shape, domain coverage.
- Added `halcytone_contracts/signals.py`:
  - `SignalPacket` pydantic v2 model (`sensor_id`, `stream`, `t_ns`, `values`, `quality`) with `quality: Field(ge=0.0, le=1.0)` and `extra="forbid"`.
  - `StreamSpec` frozen slotted dataclass (`name`, `domain`, `sample_rate_hz`, `channel_count`, `dtype`, `derived`, `archive_only`).
  - `RESERVED_STREAMS` dict covering all 21 reserved names (eeg.ch1–ch4, 5 EEG band powers, ppg, hrv.rmssd/sdnn, eda, skin_temp, imu.accel/gyro, breath acoustic/envelope/rate/phase/depth). Rates/channels chosen from README + hardware specs (Ganglion 200 Hz, EmotiBit 25 Hz PPG, Stemoscope 48 kHz acoustic archive-only, 100 Hz envelope).
- Verified: `pytest` 47 passed, `ruff check` clean, `bpsai-pair arch check halcytone_contracts/signals.py` clean.

### Session: 2026-04-17 — T1.1 Package scaffold + pyproject (Driver)

- Created `pyproject.toml` (setuptools backend, Python ≥3.11, pydantic v2 + pyyaml runtime, pytest + ruff dev extras).
- Added `halcytone_contracts/__init__.py` with `__version__ = "0.1.0"` only (exports deferred to T1.7).
- Added `tests/__init__.py`, `tests/conftest.py`, and `tests/test_package.py` (semver-shape smoke test; passes).
- Configured `[tool.ruff]` in `pyproject.toml` (line-length 100, py311 target, rules E/F/I/UP/B, excludes `.claude`, `.paircoder`, `.venv`, `build`, `dist`, `scripts`).
- Updated `.gitignore` for Python artifacts (`*.egg-info/`, `.pytest_cache/`, `dist/`, `build/`).
- Verified: clean venv `pip install -e .[dev]` succeeds, `pytest` green (1 passed), `ruff check .` clean, `bpsai-pair arch check` clean.

### Session: 2026-04-17 — Navigator handoff (sprint-1 planning)

- Loaded backlog `plans/backlogs/backlog-sprint-1.md` via `/pc-plan`.
- Pre-flight: budget healthy (info-only thresholds, no current usage warning); Trello disabled (`trello.enabled: false`).
- Created plan `plan-2026-04-sprint-1-v0-1-0-mvp` (type: `feature`, skill: `designing-and-implementing`, total Cx 32, auto-scope: story).
- Added 8 tasks (T1.1 – T1.8) via `bpsai-pair plan add-task` with per-task type/priority/complexity/sprint metadata.
- Wrote full task file bodies for each: Objective, Implementation Plan (TDD-first), Acceptance Criteria (verbatim from backlog), Verification commands, Dependencies.
- Captured wave structure + cut order for engage-time dispatch.

## What's Next

1. Sprint 1 shipped — PR [#1](https://github.com/fivedollarfridays/halcytone-contracts/pull/1) open with CI green (5/5 jobs: lint, test 3.11/3.12/3.13, schema-drift).
2. **Waiting on:** PR review + merge to `main`. After merge, tag `v0.1.0` per the versioning policy documented in the README.
3. **Next sprint (v0.2.0):** paircoder template scaffold for sibling `halcytone-*` repos + expanded `SessionManifest` (typed `baselines`, versioned `summary`). See `ROADMAP.md`.
4. **Known non-blockers carried over** from the simplify review: consider `frozen=True` on `SignalPacket` / `StateVector` (debated — defer until a downstream needs mutation); test-fixture DRY (session_id literal + sample-kwargs builders to `conftest.py`) once a second sprint's worth of tests exists to justify.

## Blockers

None.

## Integration Points (locked at planning time)

- **T1.2 → T1.7:** `RESERVED_STREAMS` feeds `validate_stream_roster`.
- **T1.4 → T1.6:** session-id regex is the single source; manifest validates `session_id` against it.
- **T1.5 → T1.7:** `SCHEMA_VERSION` re-exported as `REQUIRED_SCHEMA_VERSION`.
- **T1.6 → future CI:** `manifest.schema.json` regen diff check.
- **All wave-1 modules → T1.7:** top-level `__init__.py` re-exports.

## Out of Scope (documented in backlog)

- LSL wire-protocol wrappers, pylsl integration (lives in halcytone-sensors / halcytone-core)
- SQLAlchemy / ORM layer — each repo wraps raw DDL
- halcytone-publish ffmpeg composition logic
- Sibling-repo paircoder template (deferred to v0.2.0)
- Runtime asyncio bus for session control — models only; bus lives in halcytone-core
- PyPI publishing — v0.1.0 ships as a git dep
- Baseline format specification beyond `manifest.baselines: dict` — detailed schema is v0.3.0

## Quick Commands

```bash
# Plan inspection
bpsai-pair plan show plan-2026-04-sprint-1-v0-1-0-mvp
bpsai-pair task list --plan plan-2026-04-sprint-1-v0-1-0-mvp

# Start work
bpsai-pair task update T1.1 --status in_progress

# Complete (non-Trello)
bpsai-pair task update T1.1 --status done

# Status / budget
bpsai-pair status
bpsai-pair budget status
```
