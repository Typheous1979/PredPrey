from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QSplitter,
)
from PyQt6.QtCore import Qt, QTimer
from params.registry import ParameterRegistry
from simulation.runner import SimulationRunner
from core.events import EventBus
from core.snapshot import SimulationSnapshot
from ui.simulation_view import SimulationView
from ui.control_panel import ControlPanel
from ui.plot_panel import PlotPanel
from ui.widgets.stats_display import StatsDisplay


class MainWindow(QMainWindow):
    def __init__(self, params: ParameterRegistry, event_bus: EventBus):
        super().__init__()
        self.params    = params
        self.event_bus = event_bus
        self.runner    = SimulationRunner(params, event_bus)
        self._paused   = False

        self.setWindowTitle("Predator-Prey Genetic Simulator")
        self.resize(1400, 820)
        self._build_ui()
        self.runner.snapshot_ready.connect(self._on_snapshot)

        self._render_timer = QTimer(self)
        self._render_timer.setInterval(16)  # ~60 FPS
        self._render_timer.timeout.connect(self.sim_view.update)
        self._render_timer.start()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(4, 4, 4, 4)
        root_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left — control panel
        self.control_panel = ControlPanel(self.params)
        self.control_panel.setMinimumWidth(200)

        # Centre — canvas + button bar
        centre = QWidget()
        centre_layout = QVBoxLayout(centre)
        centre_layout.setContentsMargins(0, 0, 0, 0)
        centre_layout.setSpacing(4)

        btn_bar = self._make_button_bar()
        self.sim_view = SimulationView()

        centre_layout.addWidget(btn_bar)
        centre_layout.addWidget(self.sim_view, stretch=1)
        centre.setMinimumWidth(300)

        # Right — stats + plot
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        self.stats_display = StatsDisplay()
        self.plot_panel    = PlotPanel()

        right_layout.addWidget(self.stats_display)
        right_layout.addWidget(self.plot_panel, stretch=1)
        right.setMinimumWidth(200)

        splitter.addWidget(self.control_panel)
        splitter.addWidget(centre)
        splitter.addWidget(right)
        splitter.setSizes([340, 640, 420])

        root_layout.addWidget(splitter)

    def _make_button_bar(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)

        self.btn_start  = QPushButton("Start")
        self.btn_pause  = QPushButton("Pause")
        self.btn_reset  = QPushButton("Reset")
        self.btn_pause.setEnabled(False)

        self.btn_start.clicked.connect(self._on_start)
        self.btn_pause.clicked.connect(self._on_pause_resume)
        self.btn_reset.clicked.connect(self._on_reset)

        for btn in [self.btn_start, self.btn_pause, self.btn_reset]:
            btn.setFixedHeight(30)
            layout.addWidget(btn)
        layout.addStretch()

        legend = QLabel(
            '<span style="color:#4169e1">■</span> Prey &nbsp;'
            '<span style="color:#dc322f">■</span> Predators &nbsp;'
            '<span style="color:#228b22">■</span> Plants'
        )
        legend.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(legend)

        return bar

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_snapshot(self, snapshot: SimulationSnapshot):
        self.sim_view.render_snapshot(snapshot)   # stores snapshot; QTimer drives repaint
        self.stats_display.update_stats(snapshot)
        if snapshot.tick % 5 == 0:
            self.plot_panel.update_plot(snapshot)

    def _on_start(self):
        if not self.runner.isRunning():
            self.runner.start()
            self.btn_start.setEnabled(False)
            self.btn_pause.setEnabled(True)
        elif self._paused:
            self.runner.resume()
            self.btn_pause.setText("Pause")
            self._paused = False

    def _on_pause_resume(self):
        if not self._paused:
            self.runner.pause()
            self.btn_pause.setText("Resume")
            self._paused = True
        else:
            self.runner.resume()
            self.btn_pause.setText("Pause")
            self._paused = False

    def _on_reset(self):
        self.sim_view.clear()
        self.runner.reset()

    # ------------------------------------------------------------------

    def closeEvent(self, event):
        self.runner.stop_simulation()
        event.accept()
