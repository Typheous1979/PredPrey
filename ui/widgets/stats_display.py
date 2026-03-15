from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt
from core.snapshot import SimulationSnapshot


class StatsDisplay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        fl = QVBoxLayout(frame)
        fl.setSpacing(2)

        title = QLabel("Statistics")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 13px;")

        self.tick_label      = QLabel("Tick: 0")
        self.prey_label      = QLabel("Prey: 0")
        self.predator_label  = QLabel("Predators: 0")
        self.plant_label     = QLabel("Plants: 0")

        for w in [title, self.tick_label, self.prey_label,
                  self.predator_label, self.plant_label]:
            fl.addWidget(w)

        layout.addWidget(frame)

    def update_stats(self, snapshot: SimulationSnapshot):
        self.tick_label.setText(f"Tick: {snapshot.tick}")
        self.prey_label.setText(f"Prey: {snapshot.prey_count}")
        self.predator_label.setText(f"Predators: {snapshot.predator_count}")
        self.plant_label.setText(f"Plants: {snapshot.plant_count}")
