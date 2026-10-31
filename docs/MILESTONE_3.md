# Milestone 3 — Desktop and browser, one acquisition stream

## What changed

The standalone desktop acquisition clock from Milestone 2 has moved to the FastAPI backend. The backend owns **one `ScopeService` and one `AcquisitionEngine`**, with a bounded 4,000 samples/s history. Both PyQt and the browser consume serialized snapshots from that engine. Their plots are not two independent signal generators.

- Server: `python -m pyscopelive.server` (port 8000, loopback only)
- Browser: `http://127.0.0.1:8000/` (Canvas2D + WebSocket, no JS build step)
- Desktop: `python -m pyscopelive` (QtNetwork asynchronous HTTP snapshot polling)
- Shared signal settings: waveform, frequency, amplitude and Pause/Resume
- Local display setting: time window; changing this does not alter other clients
- `GET /api/state`, `GET /api/snapshot?window_s=0.4&max_points=1200`, `POST /api/control`, `WS /ws?window_s=0.4`

## Windows setup (Git Bash)

Start in `E:/Projects/PyScopeLive` with the project virtual environment active:

```bash
cd /e/Projects/PyScopeLive
source .venv/Scripts/activate
python -m pip install -e .
python -m pytest -q
```

**Terminal A** (leave it running):

```bash
python -m pyscopelive.server
```

**Terminal B**:

```bash
cd /e/Projects/PyScopeLive
source .venv/Scripts/activate
python -m pyscopelive
```

Open `http://127.0.0.1:8000/` in your browser.

## Verification

1. Compare the sine wave in the browser and desktop. They use the same server data (timing of individual frames can differ).
2. Change frequency or waveform in the browser and verify the desktop control changes.
3. Change amplitude in desktop and verify the browser control changes.
4. Pause in either application and confirm that **both graphs freeze**. Resume from the other.
5. Change the display time window in one client. The other client should keep its own window.
6. Stop the server: the desktop should show a disconnected message and the browser should retry. Restart it; both reconnect.
7. Run `python -m pytest -q`. Expected tests: **45 passing** on an environment with compatible dependencies (30 existing + 15 new).

## Architecture and limitations

The server is the **single acquisition owner** and is bound to `127.0.0.1` for local testing. Do **not** start multiple server instances or run Uvicorn with multiple workers: each worker would create its own engine. This is a simulated scope, not a calibrated physical oscilloscope.

Pausing stops acquisition globally. Control changes affect future samples; the existing history remains intact until overwritten. Clients poll/stream snapshots at different instants, so they share a source, not guaranteed pixel-identical frames.

The backend serializes up to 1,200 points per snapshot. Vpp and RMS are computed using the entire requested sample window, not the reduced plotting data. There is no persistence, hardware input, login, internet exposure, or high-bandwidth multi-client guarantee yet.

### Files added or changed

- `src/pyscopelive/service.py` — single-owner acquisition state
- `src/pyscopelive/server.py` — FastAPI + WebSocket
- `src/pyscopelive/web/index.html` — browser UI
- `src/pyscopelive/desktop.py` — shared-stream PyQt client
- `pyproject.toml` — web backend dependencies + browser packaging
- `tests/test_service.py`, `tests/test_server.py` — regression coverage

## Remaining work

Signal/trigger controls, multichannel support, hardware adapters, proper sample-clock sources, backpressure, security for remote exposure, CSV export, and performance measurements remain future engineering tasks. This milestone is not the finished product.
