"""Pure, deterministic signal generators used by the desktop prototype.

Times are expressed in seconds and output amplitudes in volts.
The functions in this module do not depend on Qt or any hardware.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray

SUPPORTED_WAVEFORMS = ("Sine", "Square", "Triangle")


def generate_waveform(
    kind: str,
    times_s: ArrayLike,
    frequency_hz: float,
    amplitude_v: float,
) -> NDArray[np.float64]:
    """Generate a zero-offset waveform at the requested timestamps.

    Args:
        kind: One of Sine, Square, or Triangle.
        times_s: Sampling times, in seconds.
        frequency_hz: Signal frequency; must be positive and finite.
        amplitude_v: Peak amplitude; must be nonnegative and finite.

    Returns:
        An array of simulated voltage readings in volts.
    """
    if kind not in SUPPORTED_WAVEFORMS:
        raise ValueError(f"Unknown waveform: {kind!r}")
    if not math.isfinite(frequency_hz) or frequency_hz <= 0:
        raise ValueError("frequency_hz must be positive and finite")
    if not math.isfinite(amplitude_v) or amplitude_v < 0:
        raise ValueError("amplitude_v must be nonnegative and finite")

    times = np.asarray(times_s, dtype=np.float64)
    if not np.all(np.isfinite(times)):
        raise ValueError("times_s must contain finite values")

    phase = np.remainder(times * frequency_hz, 1.0)

    if kind == "Sine":
        shape = np.sin(2.0 * np.pi * phase)
    elif kind == "Square":
        shape = np.where(phase < 0.5, 1.0, -1.0)
    else:  # Triangle: starts at +1, reaches -1 at half a period
        shape = 4.0 * np.abs(phase - 0.5) - 1.0

    return np.asarray(amplitude_v * shape, dtype=np.float64)
