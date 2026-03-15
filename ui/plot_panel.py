from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QMessageBox,
)
from PyQt6.QtCore import Qt
import pyqtgraph as pg

from core.snapshot import SimulationSnapshot
from analysis.database import SimulationDB
from analysis.analyzer import analyse_run
from ui.analysis_dialog import AnalysisDialog


class PlotPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = SimulationDB()
        self._history: list[tuple[int, int, int, int]] = []  # (tick, prey, pred, plants)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        pg.setConfigOption("background", "#1e1e1e")
        pg.setConfigOption("foreground", "#cccccc")

        # ── Save button ────────────────────────────────────────────────
        self.btn_save = QPushButton("Save Run to Database")
        self.btn_save.setFixedHeight(28)
        self.btn_save.setToolTip("Save the current run's full history to the database")
        self.btn_save.clicked.connect(self._save_run)

        # ── Saved-runs dropdown ────────────────────────────────────────
        self.run_combo = QComboBox()
        self.run_combo.setToolTip("Select a saved run to load or manage")
        self.run_combo.currentIndexChanged.connect(self._on_run_selected)

        # ── Delete / Analyze buttons ───────────────────────────────────
        action_bar = QWidget()
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(4)

        self.btn_delete = QPushButton("Delete Record")
        self.btn_delete.setFixedHeight(26)
        self.btn_delete.setToolTip("Permanently delete the selected run from the database")
        self.btn_delete.clicked.connect(self._delete_run)

        self.btn_analyze = QPushButton("Analyze")
        self.btn_analyze.setFixedHeight(26)
        self.btn_analyze.setToolTip("Analyze the selected run (Phase 2)")
        self.btn_analyze.clicked.connect(self._analyze_run)

        action_layout.addWidget(self.btn_delete)
        action_layout.addWidget(self.btn_analyze)
        action_layout.addStretch()

        # ── Plot ───────────────────────────────────────────────────────
        self.plot_widget = pg.PlotWidget(title="Population Over Time")
        self.plot_widget.setLabel("left",   "Count")
        self.plot_widget.setLabel("bottom", "Tick")
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        self.prey_curve  = self.plot_widget.plot(pen=pg.mkPen("#4169e1", width=2), name="Prey")
        self.pred_curve  = self.plot_widget.plot(pen=pg.mkPen("#dc322f", width=2), name="Predators")
        self.plant_curve = self.plot_widget.plot(pen=pg.mkPen("#228b22", width=2), name="Plants")

        layout.addWidget(self.btn_save)
        layout.addWidget(self.run_combo)
        layout.addWidget(action_bar)
        layout.addWidget(self.plot_widget)

        self._refresh_combo()
        self._update_action_buttons()

    # ------------------------------------------------------------------
    # Simulation data
    # ------------------------------------------------------------------

    def clear_history(self):
        """Call on simulation reset."""
        self._history.clear()
        self.prey_curve.setData([], [])
        self.pred_curve.setData([], [])
        self.plant_curve.setData([], [])

    def update_plot(self, snapshot: SimulationSnapshot):
        history = snapshot.stats.get("history", [])
        if not history:
            return

        n         = len(history)
        base_tick = snapshot.tick - n + 1
        ticks     = list(range(base_tick, snapshot.tick + 1))

        known = {r[0] for r in self._history}
        for t, h in zip(ticks, history):
            if t not in known:
                self._history.append((t, h[0], h[1], h[2]))

        self._history.sort(key=lambda r: r[0])
        self._draw_history(self._history)

    # ------------------------------------------------------------------
    # Database actions
    # ------------------------------------------------------------------

    def _save_run(self):
        if not self._history:
            QMessageBox.information(
                self, "No Data",
                "No run data to save yet. Start the simulation first."
            )
            return

        run_id = self._db.save_run(self._history)
        self._refresh_combo()
        # Select the newly saved run in the dropdown
        for i in range(self.run_combo.count()):
            if self.run_combo.itemData(i) == run_id:
                self.run_combo.setCurrentIndex(i)
                break
        QMessageBox.information(
            self, "Saved",
            f"Run #{run_id} saved ({len(self._history)} ticks)."
        )

    def _delete_run(self):
        run_id = self._selected_run_id()
        if run_id is None:
            return
        reply = QMessageBox.question(
            self, "Delete Run",
            f"Permanently delete Run #{run_id} from the database?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._db.delete_run(run_id)
        self._refresh_combo()
        # Restore the live run view after deletion
        self._draw_history(self._history)

    def _analyze_run(self):
        run_id = self._selected_run_id()
        if run_id is None:
            return
        rows = self._db.load_run(run_id)
        if not rows:
            QMessageBox.warning(self, "No Data", f"Run #{run_id} has no tick data.")
            return
        try:
            result = analyse_run(run_id, rows)
        except Exception as e:
            QMessageBox.critical(self, "Analysis Error", str(e))
            return
        dlg = AnalysisDialog(result, parent=self)
        dlg.exec()

    # ------------------------------------------------------------------
    # Dropdown helpers
    # ------------------------------------------------------------------

    def _refresh_combo(self):
        self.run_combo.blockSignals(True)
        self.run_combo.clear()
        runs = self._db.list_runs()
        if runs:
            for run_id, label in runs:
                self.run_combo.addItem(label, userData=run_id)
        else:
            self.run_combo.addItem("No saved runs", userData=None)
        self.run_combo.blockSignals(False)
        self._update_action_buttons()

    def _on_run_selected(self, index: int):
        run_id = self.run_combo.itemData(index)
        self._update_action_buttons()
        if run_id is None:
            return
        rows = self._db.load_run(run_id)
        self._draw_history(rows)

    def _selected_run_id(self) -> int | None:
        return self.run_combo.currentData()

    def _update_action_buttons(self):
        enabled = self._selected_run_id() is not None
        self.btn_delete.setEnabled(enabled)
        self.btn_analyze.setEnabled(enabled)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw_history(self, rows: list[tuple[int, int, int, int]]):
        if not rows:
            self.prey_curve.setData([], [])
            self.pred_curve.setData([], [])
            self.plant_curve.setData([], [])
            return
        ticks  = [r[0] for r in rows]
        prey   = [r[1] for r in rows]
        preds  = [r[2] for r in rows]
        plants = [r[3] for r in rows]
        self.prey_curve.setData(ticks,  prey)
        self.pred_curve.setData(ticks,  preds)
        self.plant_curve.setData(ticks, plants)
