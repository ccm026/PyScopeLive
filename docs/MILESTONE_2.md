# Milestone 2 — Timestamped acquisition engine

## Why the change?

Milestone 1 generated an entire synthetic waveform every time the Qt widget
redrew. That is useful as a prototype, but the readings were not acquired into
a reusable stream; an eventual browser would have generated its own waveform.

Milestone 2 introduces `AcquisitionEngine`, a UI-independent, fixed-rate,
bounded sample buffer. New measurements are produced only when the engine's
single owner calls `advance(dt_s)`. Any view can read a timestamped snapshot
without regenerating or modifying measurements.

## Implemented

- Independent `SignalSettings` and `SampleSnapshot` data classes
- Fixed-rate sampling at 4,000 samples/s by default in the desktop application
- Bounded ring history (5 seconds by default) and timestamped samples
- Safe handling of large scheduling gaps without unbounded allocation
- Immutable-on-read copies of historical samples
- Desktop graph now consumes an acquired window from the engine
- Existing waveform selection, amplitude, frequency, time window, Pause/Resume
- Vpp and RMS computed from the actual samples inside the displayed window
- Additional tests covering history, wraparound, timestamp continuity, changes
  in signal settings, long gaps and validation

## Install / test (Git Bash, Windows)

From `/e/Projects/PyScopeLive` after extracting this package into the root:

```bash
source .venv/Scripts/activate
python -m pip install -e .
python -m pytest -q
python -m pyscopelive
```

This package replaces `src/pyscopelive/desktop.py`, adds
`src/pyscopelive/acquisition.py`, adds `tests/test_acquisition.py`, and
adds this document. It does not require new dependencies or change Milestone 1
signal generation tests.

## Manual verification

1. The desktop app opens with a sine wave and status indicating 4,000 samples/s.
2. The wave scrolls when running. Press Pause: waveform freezes, label says
   `Paused`, and the button changes to Resume.
3. Resume: acquisition continues without inventing samples for paused time.
4. Switch waveform types and change frequency/amplitude. New samples reflect
   the new settings; old samples exit the visible window naturally.
5. Changing time window reads more/fewer existing samples, with no new data
   generated just because the display changed.
6. The status below the plot shows sample count, Vpp, and RMS for the window.

## Architecture and limitations

- The engine is **not thread safe**. In this milestone, the Qt event loop owns
  `advance()` and all configuration updates; rendering is read-only. The
  future web server needs a single dedicated owner (or serialized task loop)
  and must expose copies of the *same* engine's samples to all clients.
- This milestone **does not yet provide a browser UI, WebSocket endpoint, or
  hardware input**. Those remain future engineering tasks.
- The simulation samples analytically at uniform intervals. It is not a
  calibrated oscilloscope or proof of real hardware sampling performance.
- Settings changes affect *future* samples. The current graph can briefly show
  data acquired under old and new settings until the old points scroll away.
- Long scheduler gaps drop stale history to keep memory bounded.

## Next milestone

Host a single acquisition engine in a local FastAPI server and stream the
same acquired snapshots to both the desktop app and a browser through one
backend, with bounded message rates and reconnection handling. Avoid running
independent waveform generators per client.
