# Milestone 1 — Desktop oscilloscope prototype

## Implemented in this starter

- A PyQt6 desktop window with a PyQtGraph time-domain display
- Simulated sine, square, and triangle waveforms generated using NumPy
- Controls for waveform type, frequency, peak amplitude, and visible time window
- Pause/resume for the simulated display
- Window-level peak-to-peak and RMS measurements
- Pure signal math separated from UI code, with pytest coverage

The prototype does **not** receive or measure real electrical signals. The graph displays software-generated voltages, not readings from an instrument.

## Requirements

- Windows with Python 3.13 (tested by the project owner), or a compatible Python 3.12+ environment
- `requirements.txt` from the repository setup (with PyQt6, PyQtGraph, NumPy, pytest)

## Installation (Git Bash on Windows)

From the project root (`/e/Projects/PyScopeLive`):

```bash
# If another virtual environment is active, deactivate it first.
deactivate  # only if your prompt currently shows (.venv)
py -3.13 -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Run

```bash
python -m pyscopelive
```

Alternative launcher: `pyscopelive`.

## Test

```bash
python -m pytest -q
```

## Suggested manual checks

1. The window opens with a scrolling sine wave.
2. Changing frequency alters how many cycles appear within the selected time window.
3. Amplitude changes the vertical scale and waveform peak voltage.
4. Square and triangle selections produce visibly different shapes.
5. Pause freezes the waveform, and Resume restarts animation.
6. Closing the application terminates cleanly.

## Known limitations / planned engineering work

- Only synthetic signals; no physical input or calibration
- Not a real-time or calibrated measurement instrument
- The display refreshes at approximately 30 Hz, depending on system load
- No triggers, channels, cursors, FFT, recording, or browser output yet
- The upcoming browser interface should reuse a shared acquisition service rather than generate unrelated signals

Keep remaining development work documented honestly; do not call this a complete oscilloscope.
