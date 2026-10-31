"""HTTP and WebSocket integration for the single-owned acquisition service."""
import pytest
from fastapi.testclient import TestClient

from pyscopelive.server import create_app
from pyscopelive.service import ScopeService


class Clock:
    def __init__(self):
        self.t = 0.0
    def __call__(self):
        return self.t


def test_html_is_served():
    with TestClient(create_app(ScopeService(clock=Clock()))) as client:
        html = client.get("/")
        assert html.status_code == 200
        assert "PyScopeLive" in html.text
        assert "new WebSocket" in html.text


def test_http_snapshot_consistent_with_service():
    scope = ScopeService(clock=Clock())
    with TestClient(create_app(scope)) as client:
        response = client.get("/api/snapshot", params={"window_s":0.4,"max_points":500})
        assert response.status_code == 200
        data = response.json()
        assert data["count"] > 0
        assert len(data["volts_v"]) <= 500
        assert data["end_time_s"] == pytest.approx(scope.engine.elapsed_s)


def test_controls_appear_in_http_and_websocket():
    scope = ScopeService(clock=Clock())
    with TestClient(create_app(scope)) as client:
        res = client.post("/api/control",json={"waveform":"Triangle", "amplitude_v":3.0, "paused":True})
        assert res.status_code == 200
        assert client.get("/api/state").json()["paused"] is True
        with client.websocket_connect("/ws?window_s=0.4") as ws:
            frame = ws.receive_json()
            assert frame["state"]["waveform"] == "Triangle"
            assert frame["state"]["amplitude_v"] == 3.0
            assert frame["state"]["paused"] is True
            assert frame["count"] == client.get("/api/snapshot").json()["count"]


def test_invalid_controls_rejected_atomically():
    scope = ScopeService(clock=Clock())
    with TestClient(create_app(scope)) as client:
        for payload in ({"frequency_hz":-1},{"waveform":"Flame"},{"paused":"abc"},{"unknown":2}):
            assert client.post("/api/control",json=payload).status_code == 422
        assert client.get("/api/state").json()["frequency_hz"] == 5.0


def test_invalid_window_rejected():
    with TestClient(create_app(ScopeService(clock=Clock()))) as client:
        assert client.get("/api/snapshot?window_s=50").status_code == 422
        assert client.get("/api/snapshot?max_points=10").status_code == 422


def test_websocket_and_http_have_same_times_when_paused():
    scope = ScopeService(clock=Clock())
    with TestClient(create_app(scope)) as client:
        client.post("/api/control",json={"paused":True})
        expected = client.get("/api/snapshot?window_s=0.4&max_points=1200").json()
        with client.websocket_connect("/ws?window_s=0.4") as ws:
            actual = ws.receive_json()
        assert actual == expected
