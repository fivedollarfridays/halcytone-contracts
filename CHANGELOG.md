# Changelog

All notable changes to `halcytone-contracts` are recorded here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project follows [Semantic Versioning](https://semver.org/) with the 0.x sharpening documented in the [Versioning](README.md#versioning) section of the README (minor bumps on 0.x are treated as breaking).

## [Unreleased]

## [0.1.1] — 2026-04-17

### Changed

- Relicensed from `Proprietary` to `Apache-2.0`. Added `LICENSE` file at repo root and OSI classifier in `pyproject.toml`. The contract surface, wire format, and SQL DDL are now open under Apache 2.0 — the "broadcast" side of Halcytone remains separately licensed.
- Bumped `__contract_version__` to `0.1.1`. No schema or API changes — this is a licensing-only patch. Consumers pinned to `>=0.1,<0.2` will pick it up automatically; `check_contract_version("0.1.0")` still passes (patch-only mismatch is a no-op).

## [0.1.0] — 2026-04-17

### Added

- `halcytone_contracts.signals` — `SignalPacket` pydantic v2 model (sensor_id / stream / t_ns / values / quality with range validation), `StreamSpec` frozen dataclass, and `RESERVED_STREAMS` registry covering the full v1 stream vocabulary (EEG raw + band powers, PPG, HRV, EDA, skin temp, IMU, breath).
- `halcytone_contracts.state` — `StateVector` flat per-tick fused-frame model with `[0, 1]` validation on every `*_quality` score and all normalized fields.
- `halcytone_contracts.session` — `SessionStart`, `SessionStop`, `Annotation`, `MapperConfigUpdate` control-message models; `SessionId` validated-string alias; `SESSION_ID_REGEX` single source of truth; `format_session_id` / `parse_session_id` / `new_session_id` helpers.
- `halcytone_contracts.storage` + `storage.sql` — raw DDL for `sessions`, `baselines`, `annotations`, `state_summaries`, `meta` tables (idempotent via `CREATE TABLE IF NOT EXISTS`), `read_ddl()` loader, and `SCHEMA_VERSION` constant seeded into the `meta` table.
- `halcytone_contracts.bundles.manifest` — `SessionManifest` pydantic v2 model validated against the session-id regex, plus generated `manifest.schema.json` mirror for cross-language consumers.
- `halcytone_contracts.drift` — `ContractError`, `validate_stream_roster(published, required)`, and `check_contract_version(consumer_version)` with 0.x-sharpened semver policy (minor mismatch on 0.x hard-fails; minor mismatch on ≥1.0 warns).
- Top-level exports: `SignalPacket`, `StreamSpec`, `RESERVED_STREAMS`, `StateVector`, `SessionStart`, `SessionStop`, `Annotation`, `MapperConfigUpdate`, `SessionManifest`, `SCHEMA_VERSION`, `REQUIRED_SCHEMA_VERSION`, `__contract_version__`, `validate_stream_roster`, `check_contract_version`, `ContractError`.
- `scripts/regen_manifest_schema.py` — regenerates `manifest.schema.json` from the pydantic model; test asserts byte-equality with the checked-in file to catch drift.
- GitHub Actions CI (`.github/workflows/ci.yml`) — ruff lint, pytest across Python 3.11 / 3.12 / 3.13, manifest schema drift check on every push + PR to `main`.
- `ROADMAP.md` and this `CHANGELOG.md`.
- `README.md` Versioning section documenting the semver policy, downstream pin pattern (`halcytone-contracts>=0.1,<0.2`), and `check_contract_version` runtime pattern.

[Unreleased]: https://github.com/fivedollarfridays/halcytone-contracts/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/fivedollarfridays/halcytone-contracts/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/fivedollarfridays/halcytone-contracts/releases/tag/v0.1.0
