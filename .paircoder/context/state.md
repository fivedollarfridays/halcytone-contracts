# Current State

> Last updated: 2026-04-18

## Active Plan

**Plan:** `plan-2026-04-sprint-2-v0-2-0-typed-manifest` — Sprint 2 — halcytone-contracts v0.2.0 typed manifest
**Status:** Planned (Navigator handoff complete; ready for Driver)
**Current Sprint:** sprint-2
**Total Cx:** 17 across 5 tasks (P0 ×5)
**Source backlog:** `plans/backlogs/backlog-sprint-2.md`

## Previous Plan

**Plan:** `plan-2026-04-sprint-1-v0-1-0-mvp` — Sprint 1 — halcytone-contracts v0.1.0 MVP (shipped as v0.1.1 in PR #1; CI green, awaiting merge + `v0.1.1` tag).

## Current Focus

Tighten `SessionManifest` from two untyped dicts (`baselines`, `summary`) into fully-typed pydantic v2 models: `Baseline` + `StreamBaseline` (per-stream mean/stddev/sample_count captured during the 60s quiet window) and `SessionSummary` (versioned via `summary_schema_version: int` so AgentGrounds can evolve without breaking old bundles). Regenerate `manifest.schema.json`, bump the package to **v0.2.0**, and document the break in CHANGELOG / ROADMAP. This is a deliberate breaking minor bump under the 0.x sharpened policy — consumers pinned to `>=0.1,<0.2` must re-pin. **Scope boundary:** manifest-side schema tightening only; no fusion logic, no pylsl stubs, no PyPI publishing, no cookiecutter template (all deferred to v0.3.0).

## Task Status

### Active Sprint — sprint-2

| Task | Title | Cx | Pri | Wave | Status | Depends |
|------|-------|----|-----|------|--------|---------|
| T2.1 | Baseline + StreamBaseline pydantic models | 4 | P0 | 0 | ✓ done | — |
| T2.2 | SessionSummary pydantic model (versioned) | 4 | P0 | 0 | ✓ done | — |
| T2.3 | SessionManifest rewire + regenerated schema | 5 | P0 | 1 | ✓ done | T2.1, T2.2 |
| T2.4 | Top-level exports for Baseline + SessionSummary | 2 | P0 | 1 | pending | T2.1, T2.2 |
| T2.5 | Bump to v0.2.0 + CHANGELOG + ROADMAP | 2 | P0 | 2 | pending | T2.3, T2.4 |

### Dependency Graph

```
Wave 0:  T2.1                 T2.2                 (parallel — different module + test files)
             ↓                    ↓
Wave 1:  T2.3 (← T2.1, T2.2)  T2.4 (← T2.1, T2.2)  (parallel — manifest.py vs __init__.py)
             ↓                    ↓
Wave 2:                T2.5 (← T2.3, T2.4)         (version bump + docs)
```

### Cut Order if Budget Overflows

None — every task is P0 and strictly required to ship v0.2.0. If budget tightens, descope features (e.g., defer `summary_schema_version` to v0.2.1) by editing the backlog — do not cut tasks.

### Integration Points (locked at planning time)

- **T2.1 + T2.2 → T2.3:** `Baseline` and `SessionSummary` become `SessionManifest` field types. Import edges enforce ordering.
- **T2.1 → T2.3:** `Baseline`'s `RESERVED_STREAMS`-keyed validator makes unknown baseline streams reject at parse time — halcytone-core can't silently record baseline for a nonexistent sensor.
- **T2.3 → CI schema-drift:** `manifest.schema.json` drift check gates the PR. T2.3 must regen-and-commit the schema.
- **T2.4 → halcytone-core:** the new top-level exports are what halcytone-core's `wiring.py` imports in its own sprint-2 backlog. If T2.4 misses a name, halcytone-core's test suite breaks.
- **T2.5 → v0.2.0 tag (manual):** after this PR merges, the human operator must `git tag -a v0.2.0` and `git push origin v0.2.0`. halcytone-core's sprint-2 backlog cannot engage until that tag exists on GitHub.

### Backlog

No deprioritized items. All five backlog entries pulled into the active sprint.

## Previous Sprint — sprint-1 (completed)

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

## What Was Just Done

### Session: 2026-04-18 — T2.3 SessionManifest rewire + regenerated schema (Driver)

- TDD RED: updated `tests/test_manifest.py` to expect typed fields before changing the model — added `_example_baseline()` / `_example_summary()` helpers that build `Baseline` + `SessionSummary` shapes (multi-stream baseline with `hrv.rmssd` / `breath.rate` / `eda`; full summary including `summary_schema_version=1`), revised `test_manifest_accepts_complete_payload` to assert `.baselines.streams["hrv.rmssd"].mean`, added `test_manifest_baselines_is_typed_Baseline_model` + `test_manifest_summary_is_typed_SessionSummary_model` identity checks, breaking-change migration helpers `test_manifest_rejects_dict_shaped_baselines` / `..._summary`, cross-module `test_manifest_rejects_baseline_with_unknown_stream_key` (proves `Baseline`'s `RESERVED_STREAMS` validator fires through `SessionManifest`), and `test_manifest_yaml_roundtrip_with_populated_baseline_and_summary` covering the full v0.2.0 YAML shape. 11 failures as expected.
- TDD GREEN: rewrote `halcytone_contracts/bundles/manifest.py` — `baselines: Baseline`, `summary: SessionSummary` (replaces both `dict[str, float]` fields), added imports from `halcytone_contracts.baseline` and `halcytone_contracts.summary`, refreshed the module docstring with the v0.2.0 typing note. All `bundles/` tests green.
- Regenerated `halcytone_contracts/bundles/manifest.schema.json` via `scripts/regen_manifest_schema.py` — the new schema has a `$defs` block for `Baseline`, `StreamBaseline`, `SessionSummary` (all with correct bounds and required arrays), and the manifest's `baselines` / `summary` properties switch from `additionalProperties: number` to `$ref: '#/$defs/...'`. Idempotency verified by a second regen + diff.
- Rewrote the README manifest-example YAML block (lines 157-190) to reflect the new shape — multi-stream baseline dict with real stream names (`hrv.rmssd`, `breath.rate`, `eda`), all nine `SessionSummary` numeric fields plus `summary_schema_version`, and a trailing note that baseline keys are `RESERVED_STREAMS`-validated and the version field lets consumers branch on shape. Links to `ROADMAP.md` / `CHANGELOG.md` still resolve.
- Verified: `pytest` **336 passed** (up from 272; T2.1 + T2.2 + T2.3 coverage now included), `ruff check .` clean, `bpsai-pair arch check halcytone_contracts/bundles/manifest.py` clean, schema-drift detection working (regen output byte-equal to committed file). All 9 T2.3 ACs satisfied.
- Unblocks T2.4 (top-level exports for `Baseline` / `StreamBaseline` / `SessionSummary`) and T2.5 (v0.2.0 bump + CHANGELOG + ROADMAP).

### Session: 2026-04-17 — T2.2 SessionSummary pydantic model (versioned) (Driver)

- TDD: wrote `tests/test_summary.py` (34 tests) covering construction from sample, exact field set, **field-declaration order** (asserts `summary_schema_version` is the first field via `next(iter(model_fields))`), default-of-1 when omitted, `extra="forbid"`, schema-version bound (rejects 0 and -1, accepts higher integers like 7 so future bumps parse), parametrized `[0,1]` rejection (below-zero and above-one for each of `mean_breath_depth`, `mean_eeg_alpha`, `mean_eeg_theta`, `mean_overall_presence`, `peak_heart_breath_coherence`) plus inclusive-edge acceptance (0.0 and 1.0), `total_annotations` bound (rejects -1, accepts 0), unbounded sanity for `mean_hr`/`mean_breath_rate`, and JSON round-trip (direct + via dict).
- Added `halcytone_contracts/summary.py`: `SessionSummary` pydantic v2 model with `summary_schema_version: int = Field(default=1, ge=1)` declared first, then aggregate floats (`mean_hr`, `mean_hrv_rmssd`, `mean_breath_rate`, all unbounded by design — consumers rule on plausibility), four `[0,1]` `_Unit`-typed means and the `peak_heart_breath_coherence` `_Unit`, and `total_annotations: int = Field(ge=0)`. `extra="forbid"`, reuses the shared `Unit` alias from `signals.py` (single source of truth for `[0,1]` validation across the package).
- Module docstring includes a "Bumping `summary_schema_version`" section spelling out the contract evolution recipe (add field → increment default → consumers branch on the int) so future authors don't reinvent the rule.
- Verified: `pytest` **330 passed** (34 new + 296 carried), `ruff check .` clean, `bpsai-pair arch check halcytone_contracts/summary.py` clean. All 11 backlog ACs satisfied.

### Session: 2026-04-17 — T2.1 Baseline + StreamBaseline pydantic models (Driver)

- TDD: wrote `tests/test_baseline.py` (24 tests) covering `StreamBaseline` field set + extra="forbid", `stddev ≥ 0` bound (negative reject, zero accept for constant-signal baselines), `sample_count ≥ 1` bound (zero/negative reject, one accept), mean-allows-negative (e.g., centered eda_phasic), JSON round-trip; `Baseline` field set + extra="forbid", `duration_s ≥ 1` bound, stream-key validation against `RESERVED_STREAMS` (empty-dict reject, single unknown reject with name in message, multiple unknowns all named, all 21 reserved names accepted), full JSON round-trip (direct + via dict), and a parse-time rejection test confirming unknown streams fail during `model_validate()` not only at construct time.
- Added `halcytone_contracts/baseline.py`:
  - `StreamBaseline` pydantic v2 model: `mean: float` (unbounded — baselines may be negative for centered signals), `stddev: float = Field(ge=0.0)`, `sample_count: int = Field(ge=1)`, `extra="forbid"`.
  - `Baseline` pydantic v2 model: `streams: dict[str, StreamBaseline]`, `duration_s: int = Field(ge=1)`, `captured_at: datetime`, `extra="forbid"`.
  - `@field_validator("streams")` rejects empty dict and any keys not in `halcytone_contracts.signals.RESERVED_STREAMS`; error message lists the unknown stream names sorted alphabetically for deterministic diffs. Validator runs on both construct-time and `model_validate()` — unknown keys can't sneak through a JSON payload.
- Verified: `pytest` **296 passed** (24 new + 272 carried), `ruff check .` clean, `bpsai-pair arch check halcytone_contracts/baseline.py` clean. All 10 backlog ACs satisfied.

### Session: 2026-04-17 — Navigator handoff (sprint-2 planning)

- Loaded backlog `plans/backlogs/backlog-sprint-2.md` via `/pc-plan`.
- Pre-flight: budget healthy (info-only thresholds, no current usage warning); Trello disabled (`trello.enabled: false`) — using `designing-and-implementing` skill path.
- Created plan `plan-2026-04-sprint-2-v0-2-0-typed-manifest` (type: `feature`, skill: `designing-and-implementing`, total Cx 17, 5 tasks, P0 ×5).
  - Note: `bpsai-pair plan new` auto-slugs with a `plan-YYYY-MM-` prefix — first attempt produced a double-prefixed ID; deleted and recreated with the bare `sprint-2-...` slug.
- Added T2.1 – T2.5 via `bpsai-pair plan add-task` with per-task type/priority/complexity/sprint metadata. Task types: `feature` (T2.1, T2.2, T2.4), `refactor` (T2.3), `chore` (T2.5).
- Wrote full task file bodies for each: Objective, Implementation Plan (TDD-first), Acceptance Criteria (verbatim from backlog), Verification commands, Dependencies. Set `depends_on` YAML frontmatter by hand (CLI does not accept it).
- Verified backlog assumptions against the current repo state: `SessionManifest` still has `baselines: dict[str, float]` / `summary: dict[str, float]` (confirmed at `halcytone_contracts/bundles/manifest.py:33-34`); `__init__.py` already wired with 21 exports from sprint-1; README manifest example block lives around lines 159-170 (backlog says "around 157-168" — close enough, T2.3 will adjust whichever lines the block actually occupies at implementation time). `Unit` alias reusable from `signals.py`.
- Captured wave structure + integration points for engage-time dispatch. No cut order (all P0); descope by editing backlog, not cutting tasks.

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

1. **Wave 0 done:** T2.1 + T2.2 both green. Move to Wave 1.
2. **Wave 1:** T2.3 (manifest rewire + schema regen) and T2.4 (top-level exports) can run in parallel — they touch different files (`bundles/manifest.py` vs `__init__.py`).
3. **Wave 2:** T2.5 (version bump + CHANGELOG + ROADMAP) gates on both Wave-1 tasks and ships the release.
4. **Post-merge (human operator):** `git tag -a v0.2.0 -m "..."` and `git push origin v0.2.0`. halcytone-core's sprint-2 backlog cannot engage until that tag exists on GitHub.
5. **Sprint-1 tail:** PR [#1](https://github.com/fivedollarfridays/halcytone-contracts/pull/1) still awaiting merge + `v0.1.1` tag — track separately from this sprint.
6. **Carried non-blockers from sprint-1 simplify review:** consider `frozen=True` on `SignalPacket` / `StateVector` (deferred until a downstream needs mutation semantics); test-fixture DRY (session_id literal + sample-kwargs builders to `conftest.py`) — revisit once sprint-2 tests land to see if the duplication is large enough to justify.

## Blockers

None.

## Out of Scope (documented in backlog)

- `pylsl` type stubs (deferred to v0.3.0)
- PyPI publishing (git dep via tag stays the distribution model)
- Upper bounds on `t_ns` fields (not worth a breaking bump on its own)
- `frozen=True` on `SignalPacket` / `StateVector` (defer until a downstream needs the mutation semantics)
- Cookiecutter / paircoder template for sibling halcytone-* repos (deferred to v0.3.0)
- The broadcast / SaaS wrapper (separate private project)
- Fusion logic in halcytone-core (still consumer-stub scope; real fusion engine is a later sprint)

## Quick Commands

```bash
# Plan inspection
bpsai-pair plan show plan-2026-04-sprint-2-v0-2-0-typed-manifest
bpsai-pair task list --plan plan-2026-04-sprint-2-v0-2-0-typed-manifest

# Start work
bpsai-pair task update T2.1 --status in_progress

# Complete (non-Trello)
bpsai-pair task update T2.1 --status done

# Verify release gates locally (T2.3 / T2.5)
python scripts/regen_manifest_schema.py && git diff --exit-code halcytone_contracts/bundles/manifest.schema.json
pytest && ruff check .

# Status / budget
bpsai-pair status
bpsai-pair budget status
```
