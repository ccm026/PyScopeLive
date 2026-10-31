"""Shared stream contract and acquisition state tests, no GUI needed."""

import numpy as np
import pytest

from pyscopelive.service import ScopeService


class FakeClock:
    def __init__(self):
        self.value = 100.0

    def __call__(self):
        return self.value

    def advance(self, amount):
        self.value += amount


def test_shared_stream_readers_see_same_snapshot():
    clock = FakeClock()
    service = ScopeService(clock=clock)
    clock.advance(0.1)
    service.tick()
    a = service.snapshot(window_s=0.4)
    b = service.snapshot(window_s=0.4)
    assert a == b
    assert a["count"] >= 1000
    assert len(a["volts_v"]) <= 1200


def test_pause_freezes_acquisition_without_time_jump():
    clock = FakeClock()
    service = ScopeService(clock=clock)
    service.configure(paused=True)
    old = service.snapshot()
    clock.advance(10.0)
    service.tick()
    assert service.snapshot() == old
    service.configure(paused=False)
    clock.advance(0.1)
    service.tick()
    assert service.snapshot()["count"] > 0
    assert service.engine.elapsed_s < 1


def test_setting_change_affects_only_future_samples():
    clock = FakeClock()
    service = ScopeService(clock=clock)
    old = service.engine.snapshot(0.4)
    service.configure(waveform="Square", amplitude_v=3)
    clock.advance(0.1)
    service.tick()
    new = service.engine.snapshot(0.5)
    np.testing.assert_array_equal(new.volts_v[:old.count], old.volts_v)
    assert np.max(new.volts_v[old.count:]) == 3


def test_derived_stats_are_from_full_data_not_decimation():
    service = ScopeService(clock=FakeClock())
    s = service.snapshot(window_s=0.4, max_points=50)
    raw = service.engine.snapshot(0.4)
    assert len(s["volts_v"]) == 50
    assert s["count"] == raw.count
    assert s["vpp_v"] == pytest.approx(np.ptp(raw.volts_v))
    assert s["rms_v"] == pytest.approx(np.sqrt(np.mean(raw.volts_v ** 2)))


def test_invalid_settings_leave_state_unchanged():
    service = ScopeService(clock=FakeClock())
    start = service.state()
    with pytest.raises(ValueError):
        service.configure(waveform="Unknown")
    assert service.state() == start
    with pytest.raises(ValueError):
        service.configure(frequency_hz=300)
    assert service.state() == start


@pytest.mark.parametrize("window,points", [(0.01,1200), (3,1200), (0.4,10), (0.4,5001)])
def test_invalid_snapshot_args(window,points):
    with pytest.raises(ValueError):
        ScopeService(clock=FakeClock()).snapshot(window_s=window,max_points=points)
