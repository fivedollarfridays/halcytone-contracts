# halcytone-contracts

Shared types, schemas, and protocol specs for the Halcytone biofeedback platform. Single source of truth for how every `halcytone-*` repo talks to its neighbors. Nothing else gets built until what is in here is settled.

## Why this exists

Halcytone is a personal biofeedback sonification platform. Multiple sensors publish live signal streams, a core fusion engine aligns and combines them, and downstream modules turn the combined state into audio, visuals, and recorded sessions. All those modules live in separate repos. This one defines the shared language.

## System shape

```
Ganglion (EEG)      EmotiBit (PPG/EDA/temp/IMU)      Stemoscope (breath)
     |                     |                                |
     | native LSL          | OSC to LSL bridge              | audio to LSL bridge
     v                     v                                v
  -------------- LSL streams on localhost ---------------
                              |
                              v
                       halcytone-core
                    (fusion + session lifecycle)
                              |
          +-------------------+-------------------+
          v                   v                   v
   halcytone-audio      halcytone-hud      disk log (SQLite + XDF)
   (soundscape)         (PyQt live)        (session archive)

end of session:
  halcytone-publish composes video + audio + HUD overlay into
  ~/halcytone/sessions/{id}/ as a bundle
```

## The signal contract: SignalPacket

Every sensor adapter publishes one or more LSL streams. Each sample is equivalent to this logical record:

```python
@dataclass
class SignalPacket:
    sensor_id: str       # "ganglion-01", "emotibit-01", "stemoscope-01"
    stream: str          # "eeg.ch1", "ppg", "breath.envelope", ...
    t_ns: int            # nanoseconds since Unix epoch, LSL clock-synced
    values: list[float]  # per-sample vector
    quality: float       # 0.0 to 1.0, adapter's self-reported quality
```

LSL carries timestamps, stream names, and channel counts on the wire. SignalPacket is the python-level view. Quality is published as a separate LSL stream named `{sensor_id}.quality` so it does not pollute the signal stream.

### Stream naming convention

`{domain}.{channel}` where domain is the modality (eeg, ppg, resp, eda, imu, breath) and channel is a descriptor.

Reserved stream names for v1:

- `eeg.ch1` through `eeg.ch4` (Ganglion raw)
- `eeg.alpha`, `eeg.theta`, `eeg.beta`, `eeg.delta`, `eeg.gamma` (band power, computed in sensor adapter)
- `ppg` (EmotiBit raw)
- `hrv.rmssd`, `hrv.sdnn` (derived, 30s rolling window)
- `eda` (EmotiBit skin conductance)
- `skin_temp` (EmotiBit)
- `imu.accel`, `imu.gyro` (EmotiBit motion)
- `breath.acoustic` (Stemoscope raw, 48 kHz, archive only)
- `breath.envelope` (RMS envelope of acoustic, 100 Hz, primary live signal)
- `breath.rate`, `breath.phase`, `breath.depth` (derived from envelope, halcytone-breath)

## The state contract: StateVector

halcytone-core consumes SignalPackets and emits a fused StateVector. Every downstream module reads StateVectors, not raw signals.

```python
@dataclass
class StateVector:
    t_ns: int
    session_id: str

    # breath
    breath_phase: float              # 0.0 to 1.0 around the cycle
    breath_rate: float               # breaths per minute
    breath_depth: float              # 0.0 to 1.0 normalized to baseline
    breath_quality: float

    # cardiovascular
    heart_rate: float                # bpm
    hrv_rmssd: float                 # ms, 30s window
    hrv_quality: float

    # autonomic
    eda_level: float                 # microsiemens
    eda_phasic: float                # short-window phasic component

    # neural (Ganglion band power, normalized 0..1)
    eeg_alpha: float
    eeg_theta: float
    eeg_beta: float
    eeg_delta: float
    eeg_gamma: float
    eeg_quality: float

    # composite (computed in core)
    heart_breath_coherence: float    # 0.0 to 1.0
    overall_presence: float          # composite score
```

Flat struct by choice. Downstream modules want one frame per tick, not a bag of streams to re-align. Core aligns once, emits a flat record, done.

### Cadence

StateVector publishes at 200 Hz as a latest-value cache. Consumers read on their own cadence, no throttling or subsampling. Audio thread polls at synth rate, PyQt HUD paints at 30 Hz on its own timer. Inside core, the cache is an atomic reference updated every fusion tick.

## Session protocol

Every run creates one session.

Lifecycle:

1. **Preflight.** Core verifies each declared sensor is publishing an LSL stream. Missing sensors either abort the session or are marked optional per session config.
2. **Baseline.** 60-second quiet capture. Establishes per-session means for EDA, HRV, breath depth, EEG band power. Stored in session manifest.
3. **Active.** Live fusion, StateVector emission, downstream modules running.
4. **Teardown.** Stop capture, flush logs, invoke halcytone-publish.

Session ID format: `{YYYYMMDD}-{HHMMSS}-{slug4}` where slug4 is a 4-char random suffix. Example: `20260417-143022-k7m2`.

### Control messages (inside core only)

```python
SessionStart(session_id, config)
SessionStop()
Annotation(t_ns, label, data)       # user or module annotation
MapperConfigUpdate(params)          # live tuning of parameter mapper
```

Python messages on an asyncio in-process bus. Never leave the core process. Cross-process signals stay on LSL.

## Storage

Two formats, different purposes:

**SQLite** at `~/halcytone/halcytone.db`: session metadata, baselines, annotations, computed session summaries. Queryable for longitudinal analysis. Tables: `sessions`, `baselines`, `annotations`, `state_summaries`. Full DDL in `halcytone_contracts.storage`.

**XDF** at `~/halcytone/sessions/{id}/signals.xdf`: raw LSL recording. Every stream in the session at full sample rate, LSL timestamps preserved. Read with `pyxdf` for offline analysis.

## Session bundle (filesystem handoff)

halcytone-publish writes each completed session to:

```
~/halcytone/sessions/{session_id}/
  manifest.yaml     session metadata, sensor roster, duration, baselines, summary
  video.mp4         HUD video + soundscape audio, composed by ffmpeg
  audio.wav         soundscape only (optional standalone)
  signals.xdf       raw LSL recording
  state.jsonl       per-tick StateVector log
  notes.md          post-session notes (manual)
```

AgentGrounds (separate future project) watches `~/halcytone/sessions/` and picks up sessions where `manifest.yaml` has `ended_at` set. That field is the completion marker.

Manifest schema (shortened; full schema lives in `halcytone_contracts.bundles` and the generated `manifest.schema.json`). As of v0.2.0, `baselines` and `summary` are typed pydantic models (`Baseline`, `SessionSummary`) rather than free-form dicts:

```yaml
session_id: 20260417-143022-k7m2
started_at: 2026-04-17T14:30:22Z
ended_at: 2026-04-17T15:02:47Z
duration_s: 1945
sensors: [ganglion-01, emotibit-01, stemoscope-01]
baselines:
  streams:
    hrv.rmssd:   {mean: 48.3, stddev: 4.2, sample_count: 30}
    breath.rate: {mean:  6.2, stddev: 0.8, sample_count: 60}
    eda:         {mean:  2.1, stddev: 0.3, sample_count: 60}
  duration_s: 60
  captured_at: 2026-04-17T14:30:22Z
summary:
  summary_schema_version: 1
  mean_hr: 62.1
  mean_hrv_rmssd: 48.3
  mean_breath_rate: 6.2
  mean_breath_depth: 0.7
  mean_eeg_alpha: 0.35
  mean_eeg_theta: 0.25
  mean_overall_presence: 0.72
  peak_heart_breath_coherence: 0.68
  total_annotations: 3
artifacts:
  video: video.mp4
  audio: audio.wav
  signals: signals.xdf
  state: state.jsonl
```

Baseline stream keys are validated against `RESERVED_STREAMS` — unknown names are rejected at parse time. `summary_schema_version` lets consumers branch on shape as the summary evolves in later releases.

## Repo roster

| Repo | Role | Depends on |
|------|------|------------|
| halcytone-contracts | this repo: schemas, types, protocol | nothing |
| halcytone-core | fusion, session lifecycle, storage | contracts |
| halcytone-sensors | adapters (stemoscope, ganglion, emotibit, simulator) | contracts |
| halcytone-audio | parameter mapper + native python synth | contracts |
| halcytone-hud | PyQt live HUD | contracts |
| halcytone-breath | breath analysis (extracted later) | contracts |
| halcytone-publish | ffmpeg composer, session bundler (later) | contracts |

## Non-goals for v1

- Multi-user sessions. Single user, single rig.
- Cloud storage. Filesystem only.
- Network distribution. AgentGrounds handles that separately.
- Plugin architecture. No dynamic loading.
- Real-time audio latency SLAs. Best effort, <100ms target, not contractual.
- Hot reload. Start a new session to change config.

## Versioning

This package follows [Semantic Versioning](https://semver.org/) with one deliberate sharpening while the package is in 0.x:

| Bump kind | Meaning |
|-----------|---------|
| **major** (`1.0 → 2.0`) | Breaking contract change: a field/model/export is removed, a type changes incompatibly, or a validator tightens in a way existing producers fail. |
| **minor** (`0.1 → 0.2` or `1.0 → 1.1`) | Additive: new streams in `RESERVED_STREAMS`, new optional fields, new helpers. On ≥1.0 this is backward-compatible; on 0.x per semver §4 it is allowed to be breaking, so consumers must re-pin. |
| **patch** (`0.1.0 → 0.1.1`) | Fixes, docstring updates, test-only changes. No contract change. |

### Downstream pin recommendation

While the package is in 0.x, pin by minor band:

```toml
# pyproject.toml in a consumer repo
dependencies = [
    "halcytone-contracts>=0.1,<0.2",
]
```

Bump the upper bound deliberately when migrating to a new minor — don't let a transitive upgrade surprise you mid-session.

### Runtime contract check

Every consumer should call `check_contract_version` once at startup so a mispin crashes loud instead of failing later in a sensor-specific way:

```python
from halcytone_contracts import check_contract_version

check_contract_version("0.1.0")  # the version this consumer was developed against
```

Policy (see `halcytone_contracts/drift.py` for the table):

- exact or patch match → no-op
- minor mismatch on ≥1.0 → `UserWarning` via `warnings.warn`
- minor mismatch on 0.x → `ContractError` (strict pre-1.0 per semver §4, matches the pin band)
- major mismatch → `ContractError`

### Schema drift check

The JSON Schema mirror of `SessionManifest` at `halcytone_contracts/bundles/manifest.schema.json` is checked into the repo. CI regenerates it via `scripts/regen_manifest_schema.py` and fails on any diff, so the TypeScript side (AgentGrounds) can trust the file as the canonical cross-language contract.

### Roadmap

See [`ROADMAP.md`](ROADMAP.md) for milestone scope and [`CHANGELOG.md`](CHANGELOG.md) for released versions.

## Open design questions

As implementation surfaces new decisions, they land here with owner + target version. Forward-looking scope lives in [`ROADMAP.md`](ROADMAP.md).
