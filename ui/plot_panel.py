from PyQt6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg
from core.snapshot import SimulationSnapshot


class PlotPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        pg.setConfigOption("background", "#1e1e1e")
        pg.setConfigOption("foreground", "#cccccc")

        self.plot_widget = pg.PlotWidget(title="Population Over Time")
        self.plot_widget.setLabel("left",   "Count")
        self.plot_widget.setLabel("bottom", "Tick")
        self.plot_widget.addLegend()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        self.prey_curve    = self.plot_widget.plot(pen=pg.mkPen("#4169e1", width=2), name="Prey")
        self.pred_curve    = self.plot_widget.plot(pen=pg.mkPen("#dc322f", width=2), name="Predators")
        self.plant_curve   = self.plot_widget.plot(pen=pg.mkPen("#228b22", width=2), name="Plants")

        layout.addWidget(self.plot_widget)

    def update_plot(self, snapshot: SimulationSnapshot):
        history = snapshot.stats.get("history", [])
        if not history:
            return
        n = len(history)
        base_tick = snapshot.tick - n + 1
        ticks  = list(range(base_tick, snapshot.tick + 1))
        prey   = [h[0] for h in history]
        preds  = [h[1] for h in history]
        plants = [h[2] for h in history]
        self.prey_curve.setData(ticks, prey)
        self.pred_curve.setData(ticks, preds)
        self.plant_curve.setData(ticks, plants)
