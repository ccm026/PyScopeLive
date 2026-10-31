"""Single-owner acquisition state shared by HTTP, WebSocket and desktop clients.

One FastAPI event loop owns this service. Do not run Uvicorn with multiple
worker processes: doing so would create multiple independent acquisitions.
"""
from __future__ import annotations

from time import monotonic
import math
import numpy as np

from .acquisition import AcquisitionEngine
from .signals import SUPPORTED_WAVEFORMS


class ScopeService:
    def __init__(self, *, clock=monotonic) -> None:
        self.engine = AcquisitionEngine(sample_rate_hz=4000, history_s=5.0)
        self.paused = False
        self._clock = clock
        self._last_tick = clock()
        # Prefill the screen so new clients see meaningful data immediately.
        self.engine.advance(0.4)

    def tick(self) -> None:
        now = self._clock()
        dt = max(0.0, now - self._last_tick)
        self._last_tick = now
        if not self.paused:
            self.engine.advance(dt)

    def configure(self, *, waveform=None, frequency_hz=None, amplitude_v=None, paused=None) -> dict:
        if waveform is not None and waveform not in SUPPORTED_WAVEFORMS:
            raise ValueError("Unknown waveform")
        if frequency_hz is not None and (not math.isfinite(frequency_hz) or not 0.5 <= frequency_hz <= 100.0):
            raise ValueError("Frequency must be between 0.5 and 100 Hz")
        if amplitude_v is not None and (not math.isfinite(amplitude_v) or not 0.1 <= amplitude_v <= 10.0):
            raise ValueError("Amplitude must be between 0.1 and 10 V")
        if paused is not None and not isinstance(paused, bool):
            raise ValueError("paused must be a boolean")
        self.tick()  # Capture time up to the settings change before applying it.
        self.engine.configure(waveform=waveform, frequency_hz=frequency_hz, amplitude_v=amplitude_v)
        if paused is not None:
            self.paused = paused
        return self.state()

    def state(self) -> dict:
        s = self.engine.settings
        return {
            "waveform": s.waveform,
            "frequency_hz": s.frequency_hz,
            "amplitude_v": s.amplitude_v,
            "paused": self.paused,
            "sample_rate_hz": self.engine.sample_rate_hz,
            "history_s": self.engine.history_s,
        }

    def snapshot(self, *, window_s: float = 0.4, max_points: int = 1200) -> dict:
        if not math.isfinite(window_s) or not 0.05 <= window_s <= 2.0:
            raise ValueError("window_s must be between 0.05 and 2 seconds")
        if not isinstance(max_points, int) or not 50 <= max_points <= 5000:
            raise ValueError("max_points must be between 50 and 5000")
        snap = self.engine.snapshot(window_s)
        n = snap.count
        if n:
            # Downsample only the serialized display data; statistics are computed
            # from every acquired sample in the requested window.
            indices = np.linspace(0, n - 1, min(n, max_points), dtype=int)
            times_ms = np.round((snap.times_s[indices] - snap.end_time_s) * 1000, 3).tolist()
            volts_v = np.round(snap.volts_v[indices], 6).tolist()
            vpp = float(np.ptp(snap.volts_v))
            rms = float(np.sqrt(np.mean(snap.volts_v * snap.volts_v)))
        else:
            times_ms, volts_v, vpp, rms = [], [], None, None
        return {
            "type": "snapshot",
            "state": self.state(),
            "end_time_s": snap.end_time_s,
            "count": n,
            "times_ms": times_ms,
            "volts_v": volts_v,
            "vpp_v": vpp,
            "rms_v": rms,
        }
