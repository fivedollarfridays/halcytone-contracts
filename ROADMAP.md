# halcytone-contracts Roadmap

Scope for each release band. Dates are intentional omissions — milestones ship when the scope is covered, not by calendar.

## v0.1.0 (MVP, current)

**Goal:** pip-installable contracts package the seven-repo halcytone fleet can depend on.

- `SignalPacket` + `StreamSpec` + `RESERVED_STREAMS` registry (`halcytone_contracts.signals`)
- `StateVector` flat fused-frame model (`halcytone_contracts.state`)
- Control messages + canonical session-id format (`halcytone_contracts.session`)
- SQLite DDL + loader (`halcytone_contracts.storage` + `storage.sql`)
- `SessionManifest` + generated `manifest.schema.json` (`halcytone_contracts.bundles`)
- Drift guardrails: `__contract_version__`, `REQUIRED_SCHEMA_VERSION`, `validate_stream_roster`, `check_contract_version`, `ContractError`
- CI: ruff + pytest matrix (3.11/3.12/3.13) + manifest schema drift check
- Documented semver policy and downstream pin pattern

Out of scope: LSL wire wrappers, SQLAlchemy, ffmpeg composition, PyPI publishing, paircoder template for sibling repos.

## v0.1.x (patch band)

- Bug fixes, docstring tightening, test additions
- No schema changes — `SCHEMA_VERSION` stays at current integer
- No new exports, no new reserved streams

## v0.2.0 (next minor — breaking allowed under 0.x)

**Goal:** sibling-repo enablement + richer cross-language boundary.

- Paircoder template scaffold for sibling `halcytone-*` repos (sensors, core, audio, hud, publish)
- Expanded `SessionManifest` — versioned `summary` schema, typed `baselines` block (no longer `dict[str, float]`)
- Optional `pylsl` type stubs for consumers that want them
- Migration notes + `CHANGELOG.md` "Breaking" entry for every contract delta
- Possible: PyPI publishing once the contract has stabilized against 2+ downstream repos

## v0.3.0 (later minor)

**Goal:** tighten the data model where v0.1 left it loose.

- Detailed `Baseline` pydantic model (replaces the untyped `baselines: dict`)
- Structured `session_summary` schema (replaces the untyped `summary: dict`)
- Stream-metadata extensions: derived-from pointers, unit annotations, archive-retention policy
- SQLite DDL migration path — `SCHEMA_VERSION` bump + reference migration SQL

## v1.0.0 (stability target)

**Goal:** freeze the v1 contract. After 1.0, minor bumps are guaranteed additive-only; breaking changes require a major bump.

- All v0.x consumers in the halcytone fleet migrated and running against the candidate
- No reserved-stream churn for at least one full release cycle
- Long-term pin recommendation switches from `>=0.1,<0.2` to `>=1.0,<2.0`
