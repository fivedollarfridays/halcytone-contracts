# Sprint 2 Backlog — halcytone-contracts v0.2.0 typed manifest

## Overview

Tighten `SessionManifest` from two loose `dict` fields into fully-typed pydantic v2 models: `Baseline` + `StreamBaseline` (per-stream mean / stddev / sample_count captured during the 60s quiet window) and `SessionSummary` (versioned via `summary_schema_version: int` so AgentGrounds can evolve without breaking old bundles). Regenerate `manifest.schema.json`, bump the package to **v0.2.0**, and document the break in CHANGELOG / ROADMAP.

This is a **deliberate breaking minor bump** under the 0.x sharpened policy — consumers pinned to `>=0.1,<0.2` must re-pin. `halcytone-core` is today's only consumer and will follow in its own sprint-2 backlog (this repo must tag `v0.2.0` before core's engage can pin).

**Scope boundaries:** manifest-side schema tightening only. No fusion logic, no pylsl stubs, no PyPI publishing, no cookiecutter template — deferred to v0.3.0.

**Stack:** Python 3.11+, pydantic v2, pyyaml, pytest, ruff. Apache-2.0. Public.

## Phase 1: New typed models (Wave 0, parallel)

### T2.1 — Baseline + StreamBaseline pydantic models | Cx: 4 | P0

**Description:** Author the session-baseline contract. `StreamBaseline` captures one named stream's statistics over the 60s quiet-capture window (`mean`, `stddev ≥ 0`, `sample_count ≥ 1`). `Baseline` is the per-session envelope: a `dict[str, StreamBaseline]` keyed by reserved stream name from `RESERVED_STREAMS`, plus `duration_s` and `captured_at`. Dict keys are validated against the registry at parse time — unknown streams reject with a clear error so halcytone-core can't silently record a baseline for a nonexistent sensor.

**AC:**
- [ ] `halcytone_contracts/baseline.py` exists
- [ ] `StreamBaseline` pydantic v2 model with fields `mean: float`, `stddev: float` (validator: `ge=0`), `sample_count: int` (validator: `ge=1`); `extra="forbid"`
- [ ] `Baseline` pydantic v2 model with fields `streams: dict[str, StreamBaseline]`, `duration_s: int` (`ge=1`), `captured_at: datetime`; `extra="forbid"`
- [ ] Validator on `Baseline.streams` rejects keys not in `halcytone_contracts.signals.RESERVED_STREAMS` — error message names the unknown stream(s)
- [ ] Round-trip JSON test: `Baseline.model_validate_json(populated.model_dump_json()) == populated`
- [ ] Test: empty `streams` dict rejected with ValidationError
- [ ] Test: unknown stream name (e.g., `"not.a.real.stream"`) rejected with ValidationError that mentions the offending name
- [ ] Test: negative `stddev` rejected; zero `stddev` accepted (valid for constant-signal baselines)
- [ ] Test: `sample_count=0` rejected
- [ ] `bpsai-pair arch check halcytone_contracts/baseline.py` clean
- [ ] `ruff check .` clean

**Depends on:** none

---

### T2.2 — SessionSummary pydantic model (versioned) | Cx: 4 | P0

**Description:** Author the end-of-session summary contract. `SessionSummary` carries aggregate statistics halcytone-publish writes into `manifest.summary` after a session ends. First field is `summary_schema_version: int` (default 1, `ge=1`) so AgentGrounds can key logic off the version when the shape evolves. Numeric fields cover the statistics the fleet actually uses today; range-bounded fields (`[0, 1]`) stay bounded so downstream consumers can trust them without re-checking.

**AC:**
- [ ] `halcytone_contracts/summary.py` exists
- [ ] `SessionSummary` pydantic v2 model with `summary_schema_version: int = Field(default=1, ge=1)` as the first field
- [ ] Aggregate fields: `mean_hr: float`, `mean_hrv_rmssd: float`, `mean_breath_rate: float`, `mean_breath_depth: float` (`[0,1]`), `mean_eeg_alpha: float` (`[0,1]`), `mean_eeg_theta: float` (`[0,1]`), `mean_overall_presence: float` (`[0,1]`), `peak_heart_breath_coherence: float` (`[0,1]`), `total_annotations: int` (`ge=0`)
- [ ] `extra="forbid"`
- [ ] Round-trip JSON test
- [ ] Test: `summary_schema_version=0` rejected
- [ ] Test: out-of-range rejection for each bounded field (parametrize across `mean_breath_depth`, `mean_eeg_alpha`, `mean_eeg_theta`, `mean_overall_presence`, `peak_heart_breath_coherence`)
- [ ] Test: `total_annotations=-1` rejected
- [ ] Module docstring includes a short note on how to bump `summary_schema_version` (add field → increment version; consumers keyed on version handle the new shape)
- [ ] `bpsai-pair arch check halcytone_contracts/summary.py` clean
- [ ] `ruff check .` clean

**Depends on:** none

---

## Phase 2: Rewire + exports (Wave 1, parallel)

### T2.3 — SessionManifest rewire + regenerated schema | Cx: 5 | P0

**Description:** Replace `SessionManifest`'s two untyped dicts with the new models from T2.1 + T2.2. `baselines` becomes `Baseline`; `summary` becomes `SessionSummary`. Regenerate the JSON schema mirror (`bundles/manifest.schema.json`) via `scripts/regen_manifest_schema.py` and commit the regenerated file — the CI `schema-drift` job will fail the PR otherwise. Update `tests/test_manifest.py` sample payloads to construct real `Baseline` + `SessionSummary` instances, and update the README manifest example block to reflect the new shape.

**AC:**
- [ ] `SessionManifest.baselines: Baseline` (was `dict[str, float]`)
- [ ] `SessionManifest.summary: SessionSummary` (was `dict[str, float]`)
- [ ] `scripts/regen_manifest_schema.py` re-run; `halcytone_contracts/bundles/manifest.schema.json` committed byte-equal to regen output
- [ ] `tests/test_manifest.py` sample payloads updated — no remaining `dict[str, float]` literals for baselines/summary
- [ ] Round-trip YAML test with a fully populated `Baseline` (multi-stream) and `SessionSummary` (all fields set) passes
- [ ] Test: manifest rejects dict-shaped `baselines` or `summary` with a helpful error message (covers the breaking-change migration case)
- [ ] README.md manifest example block (around lines 157-168) updated to reflect new shape (real `Baseline` / `SessionSummary` YAML)
- [ ] README.md updated links still resolve (no dangling references)
- [ ] `ci.yml` `schema-drift` job passes locally: `python scripts/regen_manifest_schema.py && git diff --exit-code halcytone_contracts/bundles/manifest.schema.json`
- [ ] `bpsai-pair arch check halcytone_contracts/bundles/manifest.py` clean

**Depends on:** T2.1, T2.2

---

### T2.4 — Top-level exports for Baseline + SessionSummary | Cx: 2 | P0

**Description:** Expand `halcytone_contracts/__init__.py` to re-export `Baseline`, `StreamBaseline`, and `SessionSummary` at the top level. Update `tests/test_exports.py`'s `REQUIRED_EXPORTS` tuple + identity-check tests to cover the new surface. Fleet consumers (starting with halcytone-core) should write `from halcytone_contracts import Baseline, SessionSummary` without reaching into submodules.

**AC:**
- [ ] `__init__.py` imports `Baseline`, `StreamBaseline` from `halcytone_contracts.baseline` and `SessionSummary` from `halcytone_contracts.summary`
- [ ] `__init__.py` `__all__` includes `Baseline`, `StreamBaseline`, `SessionSummary` in alphabetical position
- [ ] `tests/test_exports.py::REQUIRED_EXPORTS` includes `Baseline`, `StreamBaseline`, `SessionSummary`
- [ ] `test_all_declares_required_exports` and `test_every_required_export_is_attribute` both still pass
- [ ] New identity-check test: `hc.Baseline is halcytone_contracts.baseline.Baseline`, same for `StreamBaseline` and `SessionSummary`
- [ ] `ruff check .` clean — no unused imports, no circular imports
- [ ] Fresh-import smoke: `python -c "from halcytone_contracts import Baseline, StreamBaseline, SessionSummary"` succeeds

**Depends on:** T2.1, T2.2

---

## Phase 3: Version + docs (Wave 2)

### T2.5 — Bump to v0.2.0 + CHANGELOG + ROADMAP | Cx: 2 | P0

**Description:** Cut the v0.2.0 release. Update `pyproject.toml` version and `__contract_version__` in lockstep (the `test_matches_pyproject` test enforces this). Seed a `[0.2.0]` section in `CHANGELOG.md` under Keep-a-Changelog format — include a `### Changed` subsection documenting the breaking field-type change on `SessionManifest.baselines` / `SessionManifest.summary`, and an `### Added` subsection listing the three new models. Promote v0.2.0 items from "next minor" to "shipped" in `ROADMAP.md`; promote any v0.3.0 items that are now imminent. Include an explicit migration note for consumers.

**AC:**
- [ ] `pyproject.toml` `version = "0.2.0"`
- [ ] `halcytone_contracts/__init__.py` `__contract_version__: str = "0.2.0"`
- [ ] `tests/test_exports.py::test_matches_pyproject` passes
- [ ] `CHANGELOG.md` has a `## [0.2.0] — 2026-04-17` section (or today's date), with:
  - [ ] `### Changed` listing the breaking `SessionManifest.baselines` / `SessionManifest.summary` field-type change
  - [ ] `### Added` listing `Baseline`, `StreamBaseline`, `SessionSummary`
  - [ ] Explicit migration note: "Breaking: consumers pinned to `>=0.1,<0.2` must re-pin to `>=0.2,<0.3`; `check_contract_version("0.1.x")` now hard-fails per the 0.x sharpened policy"
- [ ] CHANGELOG comparison links updated: `[Unreleased]`, `[0.2.0]`, `[0.1.1]`, `[0.1.0]`
- [ ] `ROADMAP.md`: v0.2.0 items moved from "next minor" to "shipped"; v0.3.0 items tightened based on what remains
- [ ] Full test suite green; `ruff check .` clean; schema drift check clean
- [ ] `bpsai-pair arch check .` reports no new violations

**Depends on:** T2.3, T2.4

---

## Delivery Summary

| Task | Title | Cx | Pri | Depends |
|------|-------|----|-----|---------|
| T2.1 | Baseline + StreamBaseline pydantic models | 4 | P0 | — |
| T2.2 | SessionSummary pydantic model (versioned) | 4 | P0 | — |
| T2.3 | SessionManifest rewire + regenerated schema | 5 | P0 | T2.1, T2.2 |
| T2.4 | Top-level exports for Baseline + SessionSummary | 2 | P0 | T2.1, T2.2 |
| T2.5 | Bump to v0.2.0 + CHANGELOG + ROADMAP | 2 | P0 | T2.3, T2.4 |

**Sprint Budget:** 17 Cx across 5 tasks — P0 ×5, P1 ×0, P2 ×0.

**Cut order if budget overflows:** none. Every task here is P0 and strictly required to ship v0.2.0. If budget is tight, descope by deferring features (not scope), e.g., hold `summary_schema_version` for v0.2.1 — but that would require editing this backlog, not cutting tasks from it.

## Priority Order

1. **T2.1** — Baseline (P0, wave 0, parallel)
2. **T2.2** — SessionSummary (P0, wave 0, parallel)
3. **T2.3** — SessionManifest rewire + schema regen (P0, wave 1)
4. **T2.4** — Top-level exports (P0, wave 1, parallel with T2.3)
5. **T2.5** — v0.2.0 tag + CHANGELOG + ROADMAP (P0, wave 2)

## Dependency Graph

```
Wave 0:  T2.1                 T2.2                 (parallel — different module + test files)
             ↓                    ↓
Wave 1:  T2.3 (← T2.1,T2.2)   T2.4 (← T2.1,T2.2)  (parallel — manifest.py vs __init__.py)
             ↓                    ↓
Wave 2:  T2.5 (← T2.3, T2.4)                      (version bump + docs)
```

## Integration Points

- **T2.1 + T2.2 → T2.3:** `Baseline` and `SessionSummary` become the `SessionManifest` field types. If T2.3 tries to land before T2.1/T2.2, `bundles/manifest.py` can't import — dependency edges enforce ordering.
- **T2.3 → CI schema-drift:** `manifest.schema.json` drift check gates the PR. T2.3 must regen-and-commit the schema.
- **T2.4 → halcytone-core:** the new top-level exports are what halcytone-core's `wiring.py` imports in its own sprint-2 backlog (T2.7). If T2.4 misses a name, halcytone-core's test suite breaks.
- **T2.5 → v0.2.0 tag (manual):** after this PR merges, the human operator must `git tag -a v0.2.0` and `git push origin v0.2.0`. halcytone-core's sprint-2 backlog cannot engage until that tag exists on GitHub.

## Out of Scope

- `pylsl` type stubs (deferred to v0.3.0)
- PyPI publishing (git dep via tag stays the distribution model)
- Upper bounds on `t_ns` fields (not worth a breaking bump on its own)
- `frozen=True` on `SignalPacket` / `StateVector` (defer until a downstream needs the mutation semantics)
- Cookiecutter / paircoder template for sibling halcytone-* repos (deferred to v0.3.0)
- The broadcast / SaaS wrapper (separate private project)
- Fusion logic in halcytone-core (still consumer-stub scope; real fusion engine is a later sprint)
