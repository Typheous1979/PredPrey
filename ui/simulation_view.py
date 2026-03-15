import time
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from PyQt6.QtCore import Qt
from core.snapshot import SimulationSnapshot

PLANT_COLOR    = QColor(34,  139,  34)   # forest green
PREY_COLOR     = QColor(65,  105, 225)   # royal blue
PREDATOR_COLOR = QColor(220,  50,  47)   # red
BG_COLOR       = QColor(20,   20,  20)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


class SimulationView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.snapshot: SimulationSnapshot | None = None   # current (latest)
        self._prev_snapshot: SimulationSnapshot | None = None
        self._curr_time: float = 0.0   # perf_counter when current snapshot arrived
        self._prev_time: float = 0.0   # perf_counter when previous snapshot arrived
        self.setMinimumSize(400, 400)

    def clear(self):
        self.snapshot       = None
        self._prev_snapshot = None
        self._curr_time     = 0.0
        self._prev_time     = 0.0
        self.update()

    def render_snapshot(self, snapshot: SimulationSnapshot):
        self._prev_snapshot = self.snapshot
        self._prev_time     = self._curr_time
        self.snapshot       = snapshot
        self._curr_time     = time.perf_counter()

    # ------------------------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        painter.fillRect(0, 0, w, h, BG_COLOR)

        if self.snapshot is None:
            painter.end()
            return

        snap   = self.snapshot
        prev   = self._prev_snapshot
        cell_w = w / snap.grid_width
        cell_h = h / snap.grid_height

        # Compute interpolation alpha [0, 1]
        tick_interval = self._curr_time - self._prev_time
        if prev is not None and tick_interval > 0:
            elapsed = time.perf_counter() - self._curr_time
            alpha = min(elapsed / tick_interval, 1.0)
        else:
            alpha = 1.0

        # Build previous-position lookups keyed by agent id
        prev_prey_pos  = {s.id: (s.x, s.y) for s in prev.prey_states}      if prev else {}
        prev_pred_pos  = {s.id: (s.x, s.y) for s in prev.predator_states}  if prev else {}

        # Plants  (static per tick — no interpolation needed)
        painter.setBrush(QBrush(PLANT_COLOR))
        painter.setPen(Qt.PenStyle.NoPen)
        plant_r = max(1.5, min(cell_w, cell_h) * 0.4)
        for (px, py) in snap.plant_positions:
            cx = px * cell_w + cell_w * 0.5
            cy = py * cell_h + cell_h * 0.5
            painter.drawEllipse(
                int(cx - plant_r), int(cy - plant_r),
                int(plant_r * 2), int(plant_r * 2),
            )

        # Prey  (circles)
        agent_r = max(2.0, min(cell_w, cell_h) * 0.6)
        painter.setBrush(QBrush(PREY_COLOR))
        for state in snap.prey_states:
            px0, py0 = prev_prey_pos.get(state.id, (state.x, state.y))
            ix = _lerp(px0, state.x, alpha) * cell_w + cell_w * 0.5
            iy = _lerp(py0, state.y, alpha) * cell_h + cell_h * 0.5
            painter.drawEllipse(
                int(ix - agent_r), int(iy - agent_r),
                int(agent_r * 2), int(agent_r * 2),
            )

        # Predators  (squares)
        pred_r = agent_r * 1.3
        painter.setBrush(QBrush(PREDATOR_COLOR))
        for state in snap.predator_states:
            px0, py0 = prev_pred_pos.get(state.id, (state.x, state.y))
            ix = _lerp(px0, state.x, alpha) * cell_w + cell_w * 0.5
            iy = _lerp(py0, state.y, alpha) * cell_h + cell_h * 0.5
            painter.drawRect(
                int(ix - pred_r), int(iy - pred_r),
                int(pred_r * 2), int(pred_r * 2),
            )

        painter.end()
