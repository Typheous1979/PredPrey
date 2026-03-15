import csv
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QMessageBox
import pyqtgraph as pg
from pyqtgraph.exporters import ImageExporter

from core.snapshot import SimulationSnapshot


class PlotPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        pg.setConfigOption("background", "#1e1e1e")
        pg.setConfigOption("foreground", "#cccccc")

        self.plot_widget = pg.PlotWidget(title="Population Over Time")
        self.plot_widget.setLabel("left",   "Count")
        self.plot_widget.setLabel("bottom", "Tick")
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        self.prey_curve  = self.plot_widget.plot(pen=pg.mkPen("#4169e1", width=2), name="Prey")
        self.pred_curve  = self.plot_widget.plot(pen=pg.mkPen("#dc322f", width=2), name="Predators")
        self.plant_curve = self.plot_widget.plot(pen=pg.mkPen("#228b22", width=2), name="Plants")

        # Full history accumulated across the entire run (not capped at 200)
        self._history: list[tuple[int, int, int, int]] = []  # (tick, prey, pred, plants)

        # Export buttons
        btn_bar = QWidget()
        btn_layout = QHBoxLayout(btn_bar)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(4)

        self.btn_export_csv = QPushButton("Export CSV")
        self.btn_export_csv.setFixedHeight(26)
        self.btn_export_csv.setToolTip("Save full run history to a CSV file for analysis")
        self.btn_export_csv.clicked.connect(self._export_csv)

        self.btn_export_png = QPushButton("Export Plot")
        self.btn_export_png.setFixedHeight(26)
        self.btn_export_png.setToolTip("Save the current population graph as a PNG image")
        self.btn_export_png.clicked.connect(self._export_png)

        btn_layout.addWidget(self.btn_export_csv)
        btn_layout.addWidget(self.btn_export_png)
        btn_layout.addStretch()

        layout.addWidget(self.plot_widget)
        layout.addWidget(btn_bar)

    # ------------------------------------------------------------------

    def clear_history(self):
        """Call on simulation reset to start accumulating a fresh run."""
        self._history.clear()
        self.prey_curve.setData([], [])
        self.pred_curve.setData([], [])
        self.plant_curve.setData([], [])

    def update_plot(self, snapshot: SimulationSnapshot):
        history = snapshot.stats.get("history", [])
        if not history:
            return

        n        = len(history)
        base_tick = snapshot.tick - n + 1
        ticks    = list(range(base_tick, snapshot.tick + 1))

        # Merge incoming window into full history (avoid duplicates by tick)
        known_ticks = {row[0] for row in self._history}
        for t, h in zip(ticks, history):
            if t not in known_ticks:
                self._history.append((t, h[0], h[1], h[2]))

        # Sort by tick to keep order consistent
        self._history.sort(key=lambda r: r[0])

        all_ticks  = [r[0] for r in self._history]
        all_prey   = [r[1] for r in self._history]
        all_preds  = [r[2] for r in self._history]
        all_plants = [r[3] for r in self._history]

        self.prey_curve.setData(all_ticks,  all_prey)
        self.pred_curve.setData(all_ticks,  all_preds)
        self.plant_curve.setData(all_ticks, all_plants)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _export_csv(self):
        if not self._history:
            QMessageBox.information(self, "No Data", "No history to export yet. Start the simulation first.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export History CSV", "population_history.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["tick", "prey", "predators", "plants"])
            writer.writerows(self._history)

        QMessageBox.information(self, "Exported", f"Saved {len(self._history)} rows to:\n{path}")

    def _export_png(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Plot Image", "population_plot.png",
            "PNG Images (*.png);;All Files (*)"
        )
        if not path:
            return

        exporter = ImageExporter(self.plot_widget.plotItem)
        exporter.export(path)
        QMessageBox.information(self, "Exported", f"Plot saved to:\n{path}")
