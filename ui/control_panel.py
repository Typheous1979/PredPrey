from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGroupBox, QSizePolicy, QPushButton,
)
from params.registry import ParameterRegistry
from ui.widgets.param_slider import ParamSliderWidget


class ControlPanel(QWidget):
    def __init__(self, registry: ParameterRegistry, parent=None):
        super().__init__(parent)
        self.registry = registry
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        for group_name, descriptors in sorted(self.registry.descriptors_by_group().items()):
            box = QGroupBox(group_name)
            box_layout = QVBoxLayout(box)
            box_layout.setSpacing(2)
            for desc in descriptors:
                box_layout.addWidget(ParamSliderWidget(desc, self.registry))
            layout.addWidget(box)

        layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

        self.btn_reset_defaults = QPushButton("Reset to Defaults")
        self.btn_reset_defaults.setFixedHeight(30)
        self.btn_reset_defaults.clicked.connect(self._on_reset_defaults)
        outer.addWidget(self.btn_reset_defaults)

    def _on_reset_defaults(self):
        self.registry.reset_to_defaults()
