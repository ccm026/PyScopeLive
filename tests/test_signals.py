"""Tests for signal math; no Qt application or hardware needed."""

import numpy as np
import pytest

from pyscopelive.signals import generate_waveform


def test_sine_known_points():
    times = np.array([0, 0.25, 0.5, 0.75])
    result = generate_waveform("Sine", times, frequency_hz=1.0, amplitude_v=2.0)
    np.testing.assert_allclose(result, [0, 2, 0, -2], atol=1e-12)


def test_square_known_points():
    times = np.array([0, 0.25, 0.5, 0.75])
    result = generate_waveform("Square", times, frequency_hz=1.0, amplitude_v=3.0)
    np.testing.assert_allclose(result, [3, 3, -3, -3])


def test_triangle_known_points():
    times = np.array([0, 0.25, 0.5, 0.75])
    result = generate_waveform("Triangle", times, frequency_hz=1.0, amplitude_v=2.0)
    np.testing.assert_allclose(result, [2, 0, -2, 0])


def test_zero_amplitude_produces_zero_signal():
    result = generate_waveform("Sine", np.linspace(0, 1, 12), 5.0, 0.0)
    np.testing.assert_array_equal(result, np.zeros(12))


@pytest.mark.parametrize("kind", ["Sine", "Square", "Triangle"])
def test_waveform_is_bounded(kind):
    result = generate_waveform(kind, np.linspace(0, 1, 2000), 9.0, 4.0)
    assert result.shape == (2000,)
    assert np.all(np.abs(result) <= 4.0 + 1e-12)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"kind": "Unknown", "frequency_hz": 1.0, "amplitude_v": 1.0},
        {"kind": "Sine", "frequency_hz": 0.0, "amplitude_v": 1.0},
        {"kind": "Sine", "frequency_hz": float("nan"), "amplitude_v": 1.0},
        {"kind": "Sine", "frequency_hz": 1.0, "amplitude_v": -1.0},
    ],
)
def test_invalid_configuration_rejected(kwargs):
    with pytest.raises(ValueError):
        generate_waveform(times_s=[0, 0.1], **kwargs)
