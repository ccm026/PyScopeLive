"""Unit tests for bounded sample acquisition, independent of Qt."""

import numpy as np
import pytest

from pyscopelive.acquisition import AcquisitionEngine, SignalSettings


def test_empty_snapshot_is_well_formed():
    engine = AcquisitionEngine(sample_rate_hz=100, history_s=2)
    snap = engine.snapshot(1)
    assert snap.count == 0
    assert snap.end_time_s == 0


def test_fixed_rate_no_duplicates_across_variable_updates():
    engine = AcquisitionEngine(sample_rate_hz=100, history_s=5)
    assert engine.advance(0.125) == 12
    assert engine.advance(0.125) == 13
    assert engine.advance(0.25) == 25
    snap = engine.snapshot(1)
    assert snap.count == 50
    np.testing.assert_allclose(snap.times_s, np.arange(50) / 100)
    assert len(np.unique(snap.times_s)) == 50


def test_snapshot_contains_real_generated_values():
    engine = AcquisitionEngine(sample_rate_hz=100, history_s=2,
                               settings=SignalSettings("Sine", 1.0, 2.0))
    engine.advance(1.0)
    snap = engine.snapshot(1)
    expected = 2 * np.sin(2 * np.pi * snap.times_s)
    np.testing.assert_allclose(snap.volts_v, expected, atol=1e-12)


def test_snapshot_is_copy_not_affected_by_later_samples():
    engine = AcquisitionEngine(sample_rate_hz=10, history_s=1)
    engine.advance(0.5)
    before = engine.snapshot(1)
    engine.advance(2.0)
    np.testing.assert_allclose(before.times_s, np.arange(5) / 10)
    assert before.count == 5


def test_ring_history_is_bounded_and_chronological():
    engine = AcquisitionEngine(sample_rate_hz=10, history_s=1)
    engine.advance(0.8)
    engine.advance(0.8)
    assert engine.stored_samples == 10
    assert engine.capacity == 10
    snap = engine.snapshot(1.0)
    np.testing.assert_allclose(snap.times_s, np.arange(6, 16) / 10)


def test_large_clock_jump_does_not_allocate_unlimited_history():
    engine = AcquisitionEngine(sample_rate_hz=10, history_s=1)
    engine.advance(100000.0)
    assert engine.stored_samples == 10
    snap = engine.snapshot(1.0)
    np.testing.assert_allclose(snap.times_s, np.arange(999990, 1000000) / 10)


def test_window_filters_older_samples():
    engine = AcquisitionEngine(sample_rate_hz=20, history_s=2)
    engine.advance(1.0)
    snap = engine.snapshot(0.2)
    assert snap.count == 4
    np.testing.assert_allclose(snap.times_s, [0.8, 0.85, 0.9, 0.95])


def test_reconfiguring_only_changes_future_samples():
    engine = AcquisitionEngine(sample_rate_hz=10, history_s=2,
                               settings=SignalSettings("Square", 1.0, 2.0))
    engine.advance(0.5)
    before = engine.snapshot(2)
    engine.configure(amplitude_v=4.0)
    engine.advance(0.5)
    after = engine.snapshot(2)
    np.testing.assert_array_equal(before.volts_v, after.volts_v[:5])
    np.testing.assert_allclose(np.abs(after.volts_v[5:]), 4.0)


def test_snapshot_does_not_generate_samples():
    engine = AcquisitionEngine(sample_rate_hz=100)
    engine.advance(0.2)
    count = engine.stored_samples
    for _ in range(10):
        engine.snapshot(0.1)
    assert engine.stored_samples == count


@pytest.mark.parametrize('dt', [-1.0, float('nan'), float('inf')])
def test_invalid_time_delta_rejected(dt):
    with pytest.raises(ValueError):
        AcquisitionEngine().advance(dt)


@pytest.mark.parametrize('kwargs', [
    {'sample_rate_hz': 0},
    {'sample_rate_hz': 10.5},
    {'history_s': 0},
    {'history_s': float('nan')},
    {'sample_rate_hz': 4000, 'history_s': 2000},
])
def test_invalid_buffer_configuration_rejected(kwargs):
    with pytest.raises(ValueError):
        AcquisitionEngine(**kwargs)


def test_invalid_signal_change_is_atomic():
    engine = AcquisitionEngine()
    previous = engine.settings
    with pytest.raises(ValueError):
        engine.configure(frequency_hz=-5)
    assert engine.settings == previous


def test_pause_can_be_implemented_without_catch_up():
    engine = AcquisitionEngine(sample_rate_hz=10)
    engine.advance(0.5)
    frozen = engine.snapshot(2)
    # GUI timer stopped; no advance() calls while paused.
    for _ in range(5):
        assert engine.snapshot(2).count == frozen.count
    engine.advance(0.1)
    assert engine.snapshot(2).count == frozen.count + 1
