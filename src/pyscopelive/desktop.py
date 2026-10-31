"""Non-blocking PyQt desktop view of the single PyScopeLive server stream."""
from __future__ import annotations

import json
import sys

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import QByteArray, QTimer, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtWidgets import (
    QApplication, QComboBox, QDoubleSpinBox, QGroupBox, QHBoxLayout,
    QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget,
)

from .signals import SUPPORTED_WAVEFORMS

SERVER_URL = "http://127.0.0.1:8000"


class ScopeWindow(QMainWindow):
    """Desktop controls and graph driven entirely by server samples."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyScopeLive — Shared Desktop Oscilloscope")
        self.resize(1100, 700)
        self.network = QNetworkAccessManager(self)
        self._poll_in_flight = False
        self._loaded = False
        self._paused = False

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setSpacing(12)
        self.setCentralWidget(root)

        heading = QLabel("PyScopeLive")
        heading.setStyleSheet("font-size: 25px; font-weight: bold;")
        layout.addWidget(heading)
        layout.addWidget(QLabel("Milestone 3 · Shared acquisition server · Desktop client"))
        controls = QGroupBox("Waveform controls — shared with browser")
        fields = QHBoxLayout(controls)
        layout.addWidget(controls)

        self.kind = QComboBox()
        self.kind.addItems(SUPPORTED_WAVEFORMS)
        fields.addWidget(self._field("Waveform", self.kind))

        self.frequency = QDoubleSpinBox()
        self.frequency.setRange(0.5, 100)
        self.frequency.setDecimals(1)
        self.frequency.setSingleStep(0.5)
        self.frequency.setValue(5)
        self.frequency.setSuffix(" Hz")
        fields.addWidget(self._field("Frequency", self.frequency))

        self.amplitude = QDoubleSpinBox()
        self.amplitude.setRange(0.1, 10)
        self.amplitude.setDecimals(1)
        self.amplitude.setSingleStep(0.1)
        self.amplitude.setValue(2)
        self.amplitude.setSuffix(" V")
        fields.addWidget(self._field("Peak amplitude", self.amplitude))

        self.time_window = QDoubleSpinBox()
        self.time_window.setRange(0.05, 2.0)
        self.time_window.setDecimals(2)
        self.time_window.setSingleStep(0.05)
        self.time_window.setValue(0.4)
        self.time_window.setSuffix(" s")
        fields.addWidget(self._field("Time window (local)", self.time_window))

        self.pause_button = QPushButton("Pause")
        fields.addWidget(self.pause_button)

        self.plot_widget = pg.PlotWidget(background="#0B1220")
        self.plot_widget.setLabel("left", "Voltage", units="V")
        self.plot_widget.setLabel("bottom", "Time relative to now", units="s")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.25)
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.curve = self.plot_widget.plot(pen=pg.mkPen(color="#38BDF8", width=2))
        layout.addWidget(self.plot_widget, stretch=1)
        self.stats = QLabel("Waiting for acquisition server…")
        layout.addWidget(self.stats)
        self.statusBar().showMessage(f"Connecting to {SERVER_URL}")

        self.kind.currentTextChanged.connect(lambda value: self._send_control({"waveform": value}))
        self.frequency.valueChanged.connect(lambda value: self._send_control({"frequency_hz": value}))
        self.amplitude.valueChanged.connect(lambda value: self._send_control({"amplitude_v": value}))
        self.pause_button.clicked.connect(lambda: self._send_control({"paused": not self._paused}))

        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._request_snapshot)
        self.timer.start()
        self._request_snapshot()

    @staticmethod
    def _field(label: str, widget: QWidget) -> QWidget:
        container = QWidget()
        column = QVBoxLayout(container)
        column.setContentsMargins(0, 0, 0, 0)
        column.addWidget(QLabel(label))
        column.addWidget(widget)
        return container

    def _request_snapshot(self):
        if self._poll_in_flight:
            return
        self._poll_in_flight = True
        url = f"{SERVER_URL}/api/snapshot?window_s={self.time_window.value():.2f}&max_points=1200"
        reply = self.network.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(lambda: self._receive_snapshot(reply))

    def _receive_snapshot(self, reply):
        self._poll_in_flight = False
        try:
            if reply.error().value != 0:
                raise ConnectionError(reply.errorString())
            data = json.loads(bytes(reply.readAll()).decode("utf-8"))
            self._apply_snapshot(data)
        except (ValueError, KeyError, ConnectionError) as exc:
            self._loaded = False
            self.statusBar().showMessage(f"Server disconnected — start 'python -m pyscopelive.server': {exc}")
        finally:
            reply.deleteLater()

    def _apply_snapshot(self, data):
        state = data["state"]
        self._loaded = True
        self._paused = state["paused"]
        for control, value in [
            (self.kind, state["waveform"]),
            (self.frequency, state["frequency_hz"]),
            (self.amplitude, state["amplitude_v"]),
        ]:
            control.blockSignals(True)
            try:
                if isinstance(control, QComboBox):
                    control.setCurrentText(value)
                else:
                    control.setValue(value)
            finally:
                control.blockSignals(False)
        self.pause_button.setText("Resume" if self._paused else "Pause")

        times = np.asarray(data["times_ms"], dtype=float) / 1000.0
        volts = np.asarray(data["volts_v"], dtype=float)
        self.curve.setData(times, volts)
        duration = self.time_window.value()
        self.plot_widget.setXRange(-duration, 0, padding=0)
        limit = max(0.5, state["amplitude_v"] * 1.2)
        self.plot_widget.setYRange(-limit, limit, padding=0)
        if data["count"]:
            self.stats.setText(
                f"Window Vpp: {data['vpp_v']:.2f} V    "
                f"Window RMS: {data['rms_v']:.2f} V    "
                f"Samples: {data['count']} (rendered: {len(volts)})"
            )
        else:
            self.stats.setText("Waiting for samples…")
        status = "Paused" if self._paused else "Running"
        self.statusBar().showMessage(f"{status} · Shared server · {state['sample_rate_hz']} samples/s · Simulated")

    def _send_control(self, changes):
        if not self._loaded:
            return
        request = QNetworkRequest(QUrl(f"{SERVER_URL}/api/control"))
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        reply = self.network.post(request, QByteArray(json.dumps(changes).encode("utf-8")))
        reply.finished.connect(lambda: self._finish_control(reply))

    def _finish_control(self, reply):
        if reply.error().value != 0:
            self.statusBar().showMessage(f"Control update failed: {reply.errorString()}")
        reply.deleteLater()


def main():
    app = QApplication(sys.argv)
    window = ScopeWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
