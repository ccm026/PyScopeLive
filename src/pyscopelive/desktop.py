"""PyScopeLive's first desktop oscilloscope prototype (simulation only)."""

from __future__ import annotations

import sys
from time import perf_counter

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .signals import SUPPORTED_WAVEFORMS, generate_waveform


class ScopeWindow(QMainWindow):
    """A basic time-domain oscilloscope with simulated signal sources."""

    SAMPLE_COUNT = 1600
    UPDATE_INTERVAL_MS = 33  # Roughly 30 frames per second

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PyScopeLive — Desktop Oscilloscope")
        self.resize(1100, 700)

        self._is_running = True
        self._elapsed_before_pause = 0.0
        self._resumed_at = perf_counter()

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setSpacing(12)
        self.setCentralWidget(root)

        heading = QLabel("PyScopeLive")
        heading.setStyleSheet("font-size: 25px; font-weight: bold;")
        layout.addWidget(heading)
        layout.addWidget(QLabel("Simulated signal source · Desktop prototype (Milestone 1)"))

        controls = QGroupBox("Waveform controls")
        controls_layout = QHBoxLayout(controls)
        layout.addWidget(controls)

        self.kind = QComboBox()
        self.kind.addItems(SUPPORTED_WAVEFORMS)
        controls_layout.addWidget(self._field("Waveform", self.kind))

        self.frequency = QDoubleSpinBox()
        self.frequency.setRange(0.5, 100.0)
        self.frequency.setDecimals(1)
        self.frequency.setSingleStep(0.5)
        self.frequency.setValue(5.0)
        self.frequency.setSuffix(" Hz")
        controls_layout.addWidget(self._field("Frequency", self.frequency))

        self.amplitude = QDoubleSpinBox()
        self.amplitude.setRange(0.1, 10.0)
        self.amplitude.setDecimals(1)
        self.amplitude.setSingleStep(0.1)
        self.amplitude.setValue(2.0)
        self.amplitude.setSuffix(" V")
        controls_layout.addWidget(self._field("Peak amplitude", self.amplitude))

        self.time_window = QDoubleSpinBox()
        self.time_window.setRange(0.05, 2.0)
        self.time_window.setDecimals(2)
        self.time_window.setSingleStep(0.05)
        self.time_window.setValue(0.4)
        self.time_window.setSuffix(" s")
        controls_layout.addWidget(self._field("Time window", self.time_window))

        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self._toggle_pause)
        controls_layout.addWidget(self.pause_button)

        self.plot_widget = pg.PlotWidget(background="#0B1220")
        self.plot_widget.setLabel("left", "Voltage", units="V")
        self.plot_widget.setLabel("bottom", "Time relative to now", units="s")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.25)
        self.plot_widget.setMouseEnabled(x=False, y=False)
        self.curve = self.plot_widget.plot(
            pen=pg.mkPen(color="#38BDF8", width=2)
        )
        layout.addWidget(self.plot_widget, stretch=1)

        self.stats = QLabel("Window Vpp: —    Window RMS: —")
        layout.addWidget(self.stats)
        self.statusBar().showMessage("Simulation mode · No acquisition hardware connected")

        self.timer = QTimer(self)
        self.timer.setInterval(self.UPDATE_INTERVAL_MS)
        self.timer.timeout.connect(self._update_plot)
        self._update_plot()
        self.timer.start()

    @staticmethod
    def _field(label: str, widget: QWidget) -> QWidget:
        container = QWidget()
        column = QVBoxLayout(container)
        column.setContentsMargins(0, 0, 0, 0)
        column.addWidget(QLabel(label))
        column.addWidget(widget)
        return container

    def _current_time(self) -> float:
        if self._is_running:
            return self._elapsed_before_pause + (perf_counter() - self._resumed_at)
        return self._elapsed_before_pause

    def _toggle_pause(self) -> None:
        if self._is_running:
            self._elapsed_before_pause = self._current_time()
            self._is_running = False
            self.timer.stop()
            self.pause_button.setText("Resume")
            self.statusBar().showMessage("Paused · Simulation mode")
        else:
            self._resumed_at = perf_counter()
            self._is_running = True
            self.pause_button.setText("Pause")
            self.statusBar().showMessage("Simulation mode · No acquisition hardware connected")
            self.timer.start()

    def _update_plot(self) -> None:
        duration = self.time_window.value()
        x = np.linspace(-duration, 0.0, self.SAMPLE_COUNT, endpoint=False)
        times = x + self._current_time()
        y = generate_waveform(
            kind=self.kind.currentText(),
            times_s=times,
            frequency_hz=self.frequency.value(),
            amplitude_v=self.amplitude.value(),
        )
        self.curve.setData(x, y)
        self.plot_widget.setXRange(-duration, 0.0, padding=0.0)
        y_limit = max(0.5, self.amplitude.value() * 1.2)
        self.plot_widget.setYRange(-y_limit, y_limit, padding=0.0)
        self.stats.setText(
            f"Window Vpp: {np.ptp(y):.2f} V    "
            f"Window RMS: {np.sqrt(np.mean(y * y)):.2f} V"
        )


def main() -> None:
    app = QApplication(sys.argv)
    window = ScopeWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
