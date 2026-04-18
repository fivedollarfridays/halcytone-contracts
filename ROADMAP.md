# halcytone-contracts Roadmap

Scope for each release band. Dates are intentional omissions — milestones ship when the scope is covered, not by calendar.

## v0.1.0 — shipped

**Goal:** pip-installable contracts package the seven-repo halcytone fleet can depend on.

- `SignalPacket` + `StreamSpec` + `RESERVED_STREAMS` registry (`halcytone_contracts.signals`)
- `StateVector` flat fused-frame model (`halcytone_contracts.state`)
- Control messages + canonical session-id format (`halcytone_contracts.session`)
- SQLite DDL + loader (`halcytone_contracts.storage` + `storage.sql`)
- `SessionManifest` + generated `manifest.schema.json` (`halcytone_contracts.bundles`)
- Drift guardrails: `__contract_version__`, `REQUIRED_SCHEMA_VERSION`, `validate_stream_roster`, `check_contract_version`, `ContractError`
- CI: ruff + pytest matrix (3.11/3.12/3.13) + manifest schema drift check
- Documented semver policy and downstream pin pattern

## v0.1.1 — shipped

- Relicensed to Apache-2.0 (LICENSE file + OSI classifier). No schema or API changes.
- `halcytone-contracts` and `halcytone-core` repos made public on GitHub.

## v0.2.0 — shipped (breaking under 0.x)

**Goal:** tighten the `SessionManifest` cross-language boundary.

- **`halcytone_contracts.baseline`** — typed `Baseline` + `StreamBaseline` models; `Baseline.streams` keys validated against `RESERVED_STREAMS`.
- **`halcytone_contracts.summary`** — versioned `SessionSummary` model (first field `summary_schema_version: int`, default 1) so consumers can branch on shape as summary evolves.
- **`SessionManifest` rewire** — `baselines: Baseline`, `summary: SessionSummary` (was both `dict[str, float]`).
- Regenerated `manifest.schema.json` with `$defs` block for the three new models + `$ref`s in the manifest properties.
- Top-level exports for `Baseline`, `StreamBaseline`, `SessionSummary` (public surface now 24 names).
- CHANGELOG migration note; `check_contract_version("0.1.x")` now hard-fails at runtime per the 0.x sharpened policy.

## v0.3.0 — next minor (breaking allowed under 0.x)

**Goal:** sibling-repo enablement + remaining loose ends in the data model.

- **Paircoder template scaffold** for sibling `halcytone-*` repos (sensors, audio, hud, publish, breath). Cookiecutter or `bpsai-pair template`-native.
- **Stream-metadata extensions** — derived-from pointers on `StreamSpec` (which source stream a derived one reduces from), unit annotations (SI unit per field), archive-retention policy (how long raw streams stay on disk).
- **SQLite DDL migration path** — bump `SCHEMA_VERSION`, ship a reference migration SQL for v1 → v2, document the pattern consumers follow when `SCHEMA_VERSION` changes.
- **Optional `pylsl` type stubs** for consumers that want them — out-of-repo extra install.
- **Possible:** PyPI publishing once a second downstream repo has exercised the contract end-to-end.

## v1.0.0 (stability target)

**Goal:** freeze the v1 contract. After 1.0, minor bumps are guaranteed additive-only; breaking changes require a major bump.

- All v0.x consumers in the halcytone fleet migrated and running against the candidate
- No reserved-stream churn for at least one full release cycle
- Long-term pin recommendation switches from `>=0.1,<0.2` to `>=1.0,<2.0`
