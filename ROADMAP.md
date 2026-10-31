# PyScopeLive — Development Roadmap

**Status:** Proposed future work following Milestone 3 (October 2026)

PyScopeLive already has a simulated desktop oscilloscope, a browser interface and one shared acquisition engine. The items below describe **future work that has not been completed**. Estimates are planning ranges, not logged hours, and should be revised as implementation proceeds. The project owner should keep only work they genuinely intend to pursue.

## Completed foundations (not included in future estimates)

- **Milestone 1:** PyQt6/PyQtGraph desktop prototype with sine, square and triangle waves, basic controls and signal-generation tests.
- **Milestone 2:** Timestamped, bounded acquisition engine; 4,000 simulated samples/s; Pause/Resume behavior and acquisition tests.
- **Milestone 3:** FastAPI backend with shared acquisition ownership, web oscilloscope with WebSockets, desktop HTTP client, shared controls, independent client time windows and API/service tests.

## Planned work

### 1. Multichannel acquisition and visualization — 8–12 hours

**Problem:** The application currently exposes one simulated signal. An oscilloscope should support independently configured channels and synchronized display.

**Proposed implementation:**
- Extend acquisition samples to carry channel identity without losing timestamp alignment.
- Support at least two simultaneous simulated channels with independent waveform parameters.
- Add per-channel visibility, labels, color and vertical scaling to desktop and web views.
- Keep per-channel measurements consistent across both interfaces.

**Acceptance criteria:**
- Two channels can be enabled and displayed concurrently in both clients.
- Channels share a coherent timebase while retaining independent signal settings.
- Disabling one channel does not interrupt the other.
- Regression tests cover channel creation, updates and alignment.

### 2. Edge triggering and acquisition control — 6–9 hours

**Problem:** There is no trigger mechanism to stabilize waveforms or identify meaningful events.

**Proposed implementation:**
- Add rising/falling-edge trigger selection and configurable level.
- Introduce pre-trigger/post-trigger buffering and trigger timeout behavior.
- Clarify how trigger settings interact with global Pause/Resume and both clients.

**Acceptance criteria:**
- A periodic simulated signal can be displayed around a stable trigger event.
- Trigger events and sample indices are consistent with the engine's timestamps.
- Both views display the same trigger metadata.
- Tests cover threshold crossings, noise/debounce edge cases and no-trigger cases.

### 3. Frequency analysis and FFT display — 5–8 hours

**Problem:** The project currently displays only time-domain waveforms.

**Proposed implementation:**
- Add a windowed FFT or power spectrum calculation using existing sample buffers.
- Expose frequency bins, magnitudes and sampling metadata via an API.
- Add a frequency-domain view in desktop and browser interfaces.
- Address leakage, sample-window length and aliasing limitations in documentation.

**Acceptance criteria:**
- A simulated sine wave produces a dominant peak near its configured frequency.
- FFT values are consistent between clients, with tests for known waveforms.
- The UI explains that results come from simulated samples, not calibrated hardware.

### 4. Measurement tools and cursors — 4–7 hours

**Problem:** Users can currently see Vpp and RMS but cannot measure intervals or voltage deltas interactively.

**Proposed implementation:**
- Add time and voltage cursors to each plot.
- Calculate Δt, 1/Δt and ΔV for selected points.
- Add automatic mean voltage and approximate frequency/period measurements.

**Acceptance criteria:**
- Cursor movements report correct numerical values in the current axis units.
- Measurements handle empty, paused and short-window datasets without crashing.
- Calculations are covered by deterministic tests.

### 5. Export, recording and replay — 4–7 hours

**Problem:** There is no way to persist data and reproduce a trace.

**Proposed implementation:**
- Export timestamped samples and settings to CSV.
- Add bounded local recording sessions and replay from a saved file.
- Preserve timestamp-value alignment and clearly report dropped/invalid samples.

**Acceptance criteria:**
- Export/import round trips preserve all valid values and timestamps within documented precision.
- Replay advances deterministically and Pause/Resume works.
- Data handling is verified with tests for malformed files and large recordings.

### 6. Real acquisition-source integration — 8–12 hours

**Problem:** The system cannot yet receive measurements from real devices.

**Proposed implementation:**
- Define an input-source interface that can wrap simulation and an external source.
- Prototype a safe serial/USB sample stream or supported DAQ interface.
- Add explicit sample-rate, connection-state and error-handling metadata.
- Document voltage input safety: never connect signals directly to a PC port without rated acquisition hardware.

**Acceptance criteria:**
- Source changes do not require rewriting the plotting UIs.
- Disconnections are reported and do not hang the backend.
- A replayed or mocked source can exercise the full pipeline without physical equipment.

### 7. Reliability, performance and deployment — 5–8 hours

**Problem:** The prototype has limited error handling for prolonged operation and multiple clients, and developer installation is not yet fully automated.

**Proposed implementation:**
- Add test coverage for reconnection, concurrent clients, backpressure and malformed requests.
- Benchmark sample buffering and serialization under different rates and display windows.
- Set up GitHub Actions for supported Python versions and tests.
- Consolidate development/test dependencies and document startup/error recovery.

**Acceptance criteria:**
- Tests run from a clean documented development environment.
- CI executes the test suite successfully on every pull request.
- Performance tests or documented measurements identify supported limits without making unsupported hardware claims.

## Overall planned effort

| Future workstream | Estimated effort |
| --- | ---: |
| Multichannel visualization | 8–12 hours |
| Triggering | 6–9 hours |
| FFT / frequency-domain display | 5–8 hours |
| Cursors and measurements | 4–7 hours |
| Export and replay | 4–7 hours |
| Hardware-source integration | 8–12 hours |
| Reliability, performance, CI | 5–8 hours |
| **Total prospective work** | **40–63 hours** |

These estimates exclude the completed milestones above. The plan exceeds 20 hours **only if these are tasks the owner genuinely intends to undertake**. The figures must not be reported as time already spent.

## How development will be tracked

- Create one or more genuine GitHub Issues for workstreams being undertaken.
- Use feature branches and reviewed pull requests to document substantive changes.
- Keep this roadmap up to date as features are completed or priorities change.
- Add test evidence, measurements and screenshots for real delivered functionality.
- Preserve original commit history and avoid fabricating releases, users or usage statistics.
