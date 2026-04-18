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
| T2.4 | Top-level exports for Baseline + SessionSummary | 2 | P0 | 1 | ✓ done | T2.1, T2.2 |
| T2.5 | Bump to v0.2.0 + CHANGELOG + ROADMAP | 2 | P0 | 2 | ✓ done | T2.3, T2.4 |

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

- **T2.5 done** (auto-updated by hook)

### Session: 2026-04-18 — T2.5 Bump to v0.2.0 + CHANGELOG + ROADMAP (Driver)

- Cut v0.2.0: `pyproject.toml version = "0.2.0"` and `__contract_version__ = "0.2.0"` in lockstep; `test_exports.py::test_matches_pyproject` stays green against the bumped pair.
- `CHANGELOG.md`: new `[0.2.0] — 2026-04-18` section with `### Changed` (two breaking items: `SessionManifest.baselines` and `.summary` field-type changes, regen'd schema mirror, `__contract_version__` bump under 0.x sharpened policy), `### Added` (new `baseline` + `summary` submodules, three new top-level exports — public surface 21 → 24), and a `### Migration` block pointing consumers to re-pin `>=0.2,<0.3` and rewrite any dict-literal manifest constructions. Link section updated.
- `ROADMAP.md` restructured: v0.1.0 / v0.1.1 / v0.2.0 sections marked "shipped" with concrete deliverables; v0.3.0 promoted and narrowed to "sibling-repo enablement + remaining data-model tightening" (paircoder template scaffold moved here from v0.2.0, stream-metadata extensions + DDL migration + pylsl stubs retained).
- Verified: `pytest` **336 passed**, `ruff check .` clean, schema-drift check clean (regen byte-equal to committed file). All 7 T2.5 ACs satisfied.
- **Sprint 2 complete:** 5/5 tasks done; v0.2.0 ready to tag once the PR merges. Halcytone-core sprint-2 backlog unblocks as soon as the `v0.2.0` tag is pushed.

### Session: 2026-04-18 — T2.4 Top-level exports for Baseline + SessionSummary (Driver)

- TDD: added `Baseline`, `StreamBaseline`, `SessionSummary` to `tests/test_exports.py::REQUIRED_EXPORTS` (now 24 names) and expanded `test_models_identity_matches_submodules` with identity assertions for the three new classes. Confirmed RED via `AttributeError: module 'halcytone_contracts' has no attribute 'Baseline'`.
- Implemented: `halcytone_contracts/__init__.py` imports `Baseline, StreamBaseline` from `halcytone_contracts.baseline` and `SessionSummary` from `halcytone_contracts.summary`; all three added to `__all__` in alphabetical slot. Submodule import order stays bottom-up (signals → baseline → summary → session → drift → bundles → state → storage) so no circular imports.
- Verified: `pytest` **336 passed** (all, incl. the 10 in `test_exports.py`), `ruff check .` clean, `python -c "from halcytone_contracts import Baseline, StreamBaseline, SessionSummary"` succeeds. All 6 T2.4 ACs satisfied.
- Unblocks T2.5 (v0.2.0 bump + CHANGELOG + ROADMAP).

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

### Sprint 1 — archived

Full session details (T1.1–T1.8 + review-and-fix + navigator handoff) live in [`.paircoder/archive/sprint-1-sessions.md`](../archive/sprint-1-sessions.md). Sprint shipped as v0.1.0 (with a v0.1.1 relicense follow-up) via PR [#1](https://github.com/fivedollarfridays/halcytone-contracts/pull/1).

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
