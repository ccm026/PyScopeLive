"""Timestamped, bounded simulation acquisition shared by display consumers.

The engine is deliberately UI-agnostic. One owner advances the engine on its
clock; multiple clients may read the resulting sample snapshots. Milestone 2
uses a Qt timer as that owner. A later server milestone will own the clock and
make the same samples available to desktop and web clients.

All times are seconds relative to the simulation start; voltages are volts.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import math

import numpy as np
from numpy.typing import NDArray

from .signals import SUPPORTED_WAVEFORMS, generate_waveform


@dataclass(frozen=True)
class SignalSettings:
    waveform: str = "Sine"
    frequency_hz: float = 5.0
    amplitude_v: float = 2.0

    def __post_init__(self) -> None:
        if self.waveform not in SUPPORTED_WAVEFORMS:
            raise ValueError(f"Unsupported waveform: {self.waveform!r}")
        if not math.isfinite(self.frequency_hz) or self.frequency_hz <= 0:
            raise ValueError("frequency_hz must be positive and finite")
        if not math.isfinite(self.amplitude_v) or self.amplitude_v < 0:
            raise ValueError("amplitude_v must be nonnegative and finite")


@dataclass(frozen=True)
class SampleSnapshot:
    """Copy of sampled data; safe to keep across later acquisitions."""

    times_s: NDArray[np.float64]
    volts_v: NDArray[np.float64]
    end_time_s: float

    @property
    def count(self) -> int:
        return int(self.times_s.size)


class AcquisitionEngine:
    """Sample a source on a fixed time grid into bounded chronological history.

    ``advance(dt_s)`` is the *only* method that generates new samples.
    ``snapshot(window_s)`` never synthesizes new data. This separation will
    allow multiple interfaces to render exactly the same acquired stream.

    The engine is not thread-safe: keep a single owner for configuration and
    acquisition. A future server will use one serialized acquisition loop.
    """

    def __init__(
        self,
        *,
        sample_rate_hz: int = 4000,
        history_s: float = 5.0,
        settings: SignalSettings | None = None,
    ) -> None:
        if isinstance(sample_rate_hz, bool) or not isinstance(sample_rate_hz, int) or sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be a positive integer")
        if not math.isfinite(history_s) or history_s <= 0:
            raise ValueError("history_s must be positive and finite")
        capacity = int(math.ceil(sample_rate_hz * history_s))
        if capacity < 1 or capacity > 2_000_000:
            raise ValueError("history capacity must contain 1 to 2,000,000 samples")

        self.sample_rate_hz = sample_rate_hz
        self.history_s = history_s
        self.settings = settings if settings is not None else SignalSettings()
        self._capacity = capacity
        self._times = np.empty(capacity, dtype=np.float64)
        self._volts = np.empty(capacity, dtype=np.float64)
        self._write_at = 0
        self._size = 0
        self._sample_cursor = 0
        self.elapsed_s = 0.0

    @property
    def stored_samples(self) -> int:
        return self._size

    @property
    def capacity(self) -> int:
        return self._capacity

    def configure(
        self,
        *,
        waveform: str | None = None,
        frequency_hz: float | None = None,
        amplitude_v: float | None = None,
    ) -> None:
        """Change only future samples, preserving already acquired history."""
        self.settings = replace(
            self.settings,
            waveform=self.settings.waveform if waveform is None else waveform,
            frequency_hz=self.settings.frequency_hz if frequency_hz is None else frequency_hz,
            amplitude_v=self.settings.amplitude_v if amplitude_v is None else amplitude_v,
        )

    def advance(self, dt_s: float) -> int:
        """Advance simulation time and acquire new fixed-rate samples.

        Returns the number of new samples *stored*. If an unusually large
        clock jump exceeds the history capacity, old data is discarded and
        only the newest ``capacity`` samples are generated.
        """
        if not math.isfinite(dt_s) or dt_s < 0:
            raise ValueError("dt_s must be nonnegative and finite")
        self.elapsed_s += dt_s
        target = math.floor(self.elapsed_s * self.sample_rate_hz + 1e-9)
        missing = target - self._sample_cursor
        if missing <= 0:
            return 0

        if missing > self._capacity:
            # Resynchronize after a long sleep without allocating huge arrays.
            self._size = 0
            self._write_at = 0
        first = max(self._sample_cursor, target - self._capacity)
        indices = np.arange(first, target, dtype=np.int64)
        timestamps = indices.astype(np.float64) / self.sample_rate_hz
        voltage = generate_waveform(
            self.settings.waveform,
            timestamps,
            self.settings.frequency_hz,
            self.settings.amplitude_v,
        )
        self._append(timestamps, voltage)
        self._sample_cursor = target
        return len(indices)

    def _append(self, times: NDArray[np.float64], volts: NDArray[np.float64]) -> None:
        n = len(times)
        if not n:
            return
        first_part = min(n, self._capacity - self._write_at)
        self._times[self._write_at:self._write_at + first_part] = times[:first_part]
        self._volts[self._write_at:self._write_at + first_part] = volts[:first_part]
        remaining = n - first_part
        if remaining:
            self._times[:remaining] = times[first_part:]
            self._volts[:remaining] = volts[first_part:]
        self._write_at = (self._write_at + n) % self._capacity
        self._size = min(self._capacity, self._size + n)

    def snapshot(self, window_s: float) -> SampleSnapshot:
        """Return recent *acquired* samples, without mutating the engine."""
        if not math.isfinite(window_s) or window_s <= 0:
            raise ValueError("window_s must be positive and finite")
        if not self._size:
            return SampleSnapshot(np.array([], dtype=np.float64), np.array([], dtype=np.float64), self.elapsed_s)

        start = (self._write_at - self._size) % self._capacity
        end = start + self._size
        if end <= self._capacity:
            t = self._times[start:end].copy()
            v = self._volts[start:end].copy()
        else:
            split = end - self._capacity
            t = np.concatenate((self._times[start:], self._times[:split]))
            v = np.concatenate((self._volts[start:], self._volts[:split]))

        # Times on the lower edge belong to the selected window.
        mask = t >= (self.elapsed_s - window_s - 1e-10)
        return SampleSnapshot(t[mask], v[mask], self.elapsed_s)
