# PyScopeLive

**A Python desktop and browser oscilloscope powered by one shared acquisition stream.**

PyScopeLive is an independently developed software project for visualizing simulated voltage signals in real time. It provides a desktop oscilloscope built with **PyQt6** and **PyQtGraph** and a browser interface served by **FastAPI**. Both interfaces read the same timestamped samples from one backend acquisition engine.

> **Current status: working simulation prototype (Milestone 3).** PyScopeLive does not yet connect to physical measurement hardware. Its readings are simulated, not calibrated, and must not be used as electrical measurements.

## Features implemented

- **Two interfaces:** native PyQt6 desktop application and a browser-based oscilloscope.
- **Shared data source:** one FastAPI server owns the acquisition engine; desktop and browser receive the same underlying samples.
- **Simulated signals:** sine, square, and triangle waveforms.
- **Live controls:** waveform selection, frequency (0.5–100 Hz), peak amplitude (0.1–10 V), and global Pause/Resume.
- **Independent viewing windows:** each client selects its own time window (0.05–2 seconds); changing it does not alter the other client.
- **Timestamped history:** simulated acquisition at 4,000 samples/s with a bounded five-second buffer.
- **Measurements:** peak-to-peak voltage (Vpp) and RMS for samples in the requested display window.
- **Streaming and reconnecting:** WebSocket updates for the browser and asynchronous HTTP polling for the desktop.
- **Tests:** signal generation, acquisition, service behavior, HTTP and WebSocket endpoints.

## Application architecture

```text
Simulated signal generator
         |
         v
AcquisitionEngine (4,000 samples/s; 5-second history)
         |
         v
ScopeService (single owner of samples and shared settings)
         |
         v
FastAPI server (127.0.0.1:8000)
         |
         +--> HTTP API --> PyQt6 + PyQtGraph desktop application
         |
         +--> WebSocket --> HTML5 Canvas browser application
```

All clients share **signal settings and acquisition state**, but each client controls its **own display time window**. Differences in refresh timing may cause plots to look slightly offset even though they use one source.

The backend currently runs as one local process with one worker. Starting multiple server worker processes would create separate acquisition engines and break the single-stream assumption.

## Technology stack

| Component | Technology |
| --- | --- |
| Application logic | Python 3.13 used during Windows development; package declares Python >=3.12 |
| Numerical signals | NumPy |
| Desktop GUI | PyQt6 |
| Desktop plots | PyQtGraph |
| Server and API | FastAPI + Uvicorn |
| Browser interface | HTML5 Canvas + JavaScript + WebSocket |
| Automated testing | pytest + FastAPI/Starlette TestClient |

## Getting started on Windows (Git Bash)

### Prerequisites

- Python 3.12 or newer (development tested using Python 3.13).
- Git.
- A desktop environment for the PyQt window and a modern web browser for the web interface.

### 1. Clone the repository

```bash
git clone https://github.com/ccm026/PyScopeLive.git
cd PyScopeLive
```

### 2. Set up a project-specific Python environment

```bash
py -3.13 -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Use a different installed, supported version if Python 3.13 is unavailable (for example `py -3.12`). The `.venv` folder should not be committed.

### 3. Start the shared backend (Terminal A)

```bash
python -m pyscopelive.server
```

Leave this terminal running. The backend listens at **http://127.0.0.1:8000** by default.

### 4. Start the desktop app (Terminal B)

Open a second Git Bash terminal:

```bash
cd /e/Projects/PyScopeLive   # replace with your actual local repository folder
source .venv/Scripts/activate
python -m pyscopelive
```

If you cloned elsewhere, use the actual path instead. The desktop needs the backend from Terminal A to be running.

### 5. Open the browser interface

Visit **http://127.0.0.1:8000/** in a browser on the same computer.

Try changing the frequency or amplitude in either interface: both clients should reflect the updated settings. Pause/Resume is shared. The time-window setting is deliberately local to each interface.

## Running the tests

Within the activated virtual environment:

```bash
python -m pip install pytest httpx2
python -m pytest -q
```

`httpx2` is used by the currently tested FastAPI/Starlette TestClient environment. Test dependencies will be consolidated into a documented development dependency group as future cleanup. This command is intended for the environment used during the Milestone 3 validation; package dependency compatibility may change in later releases.

## Local API

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Browser oscilloscope |
| `GET /api/state` | Current shared acquisition settings |
| `GET /api/snapshot?window_s=0.4&max_points=1200` | Timestamped samples and measurements |
| `POST /api/control` | Update waveform, frequency, amplitude or Pause/Resume |
| `WS /ws?window_s=0.4` | Browser stream of snapshots |

The server is currently bound to **127.0.0.1** for local use only. It has no authentication or access restrictions appropriate for internet exposure. Do not change the bind address to a public interface without adding appropriate security measures.

## Repository structure

```text
PyScopeLive/
├── src/pyscopelive/
│   ├── signals.py        # Waveform generation
│   ├── acquisition.py    # Timestamped history and sampling
│   ├── service.py        # Shared acquisition state and controls
│   ├── server.py         # FastAPI + WebSocket server
│   ├── desktop.py        # PyQt6 desktop client
│   ├── __main__.py       # python -m pyscopelive
│   └── web/index.html    # Browser UI
├── tests/                # Signal, acquisition, API and service tests
├── docs/                 # Milestone notes
├── pyproject.toml        # Python package configuration
├── README.md
└── ROADMAP.md             # Planned future development (if present)
```

## Current limitations

- **Simulated input only:** no physical oscilloscope, ADC, serial, USB or network acquisition adapter is connected.
- **Single channel:** no multichannel alignment, triggering, FFT, measurement cursors or recording/replay yet.
- **Local development server:** one backend process and worker; no remote authentication or production deployment configuration.
- **Sampling simulation:** the 4,000 samples/s rate represents software-generated data; it is not a verified hardware sampling rate.
- **Display:** clients render snapshots at their own refresh times, so pixels are not guaranteed to be identical frame by frame.

## Project roadmap

See [ROADMAP.md](ROADMAP.md) for future engineering work, estimated effort and acceptance criteria. The roadmap is prospective: the features there are **not implemented yet**.

## Project background

PyScopeLive is my independent personal software project, created to explore oscilloscope visualization, real-time data acquisition architecture and Python desktop/web development. I retain ownership of the project and intend to continue building and maintaining it.

## License

See [LICENSE](LICENSE) for the repository's actual license terms. **PyQt6's free distribution is GPLv3-licensed**, so verify the repository's license is appropriate before distributing the application. The CC-CLI v2 program accepts GPL-family licenses only through its additional-approval process.

## Feedback

Issues and suggestions are welcome through GitHub Issues. Please do not post API keys, passwords or personal information.
