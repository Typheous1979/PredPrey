from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QSlider, QLineEdit, QPushButton, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from params.descriptor import ParameterDescriptor
from params.registry import ParameterRegistry


class ParamSliderWidget(QWidget):
    value_changed = pyqtSignal(str, float)

    def __init__(
        self,
        descriptor: ParameterDescriptor,
        registry: ParameterRegistry,
        parent=None,
    ):
        super().__init__(parent)
        self.descriptor = descriptor
        self.registry = registry
        self._updating = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 1, 2, 1)
        layout.setSpacing(4)

        # Label
        self.label = QLabel(descriptor.label)
        self.label.setFixedWidth(180)
        self.label.setToolTip(descriptor.tooltip)
        self.label.setToolTipDuration(10000)

        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.slider.setToolTip(descriptor.tooltip)
        self.slider.setToolTipDuration(10000)

        # Minus button
        self.btn_minus = QPushButton("−")
        self.btn_minus.setFixedSize(24, 24)
        self.btn_minus.setToolTip(f"Decrease by {descriptor.step}  (hold to repeat)")
        self.btn_minus.setToolTipDuration(10000)

        # Read-only value display
        self.value_display = QLineEdit()
        self.value_display.setFixedWidth(72)
        self.value_display.setReadOnly(True)
        self.value_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_display.setToolTip(descriptor.tooltip)
        self.value_display.setToolTipDuration(10000)

        # Plus button
        self.btn_plus = QPushButton("+")
        self.btn_plus.setFixedSize(24, 24)
        self.btn_plus.setToolTip(f"Increase by {descriptor.step}  (hold to repeat)")
        self.btn_plus.setToolTipDuration(10000)

        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        layout.addWidget(self.btn_minus)
        layout.addWidget(self.value_display)
        layout.addWidget(self.btn_plus)

        self._set_display(registry.get(descriptor.key))

        self.slider.valueChanged.connect(self._on_slider_changed)
        self._attach_hold_repeat(self.btn_minus, self._on_minus)
        self._attach_hold_repeat(self.btn_plus,  self._on_plus)
        registry.on_change(descriptor.key, self._on_registry_changed)

    # ------------------------------------------------------------------
    # Hold-to-repeat with acceleration
    # ------------------------------------------------------------------

    def _attach_hold_repeat(self, btn: QPushButton, step_fn):
        """Wire pressed/released on btn so holding accelerates step_fn."""
        timer = QTimer(self)
        timer.setSingleShot(False)
        count = [0]

        def on_press():
            step_fn()                  # immediate step on first press
            count[0] = 0
            timer.setInterval(350)     # initial delay before repeating
            timer.start()

        def on_tick():
            step_fn()
            count[0] += 1
            # Accelerate through four speed tiers
            if count[0] == 3:
                timer.setInterval(150)
            elif count[0] == 8:
                timer.setInterval(75)
            elif count[0] == 16:
                timer.setInterval(35)

        def on_release():
            timer.stop()
            count[0] = 0

        btn.pressed.connect(on_press)
        timer.timeout.connect(on_tick)
        btn.released.connect(on_release)

    # ------------------------------------------------------------------

    def _val_to_slider(self, val: float) -> int:
        span = self.descriptor.max_val - self.descriptor.min_val
        if span == 0:
            return 0
        return int((val - self.descriptor.min_val) / span * 1000)

    def _slider_to_val(self, pos: int):
        span = self.descriptor.max_val - self.descriptor.min_val
        val  = self.descriptor.min_val + (pos / 1000.0) * span
        return self.descriptor.dtype(val)

    def _format(self, val) -> str:
        if self.descriptor.dtype == int:
            return str(int(val))
        return f"{val:.4g}"

    def _set_display(self, val):
        self._updating = True
        self.slider.setValue(self._val_to_slider(val))
        self.value_display.setText(self._format(val))
        self._updating = False

    # ------------------------------------------------------------------

    def _on_slider_changed(self, pos: int):
        if self._updating:
            return
        val = self._slider_to_val(pos)
        self._updating = True
        self.value_display.setText(self._format(val))
        self._updating = False
        self.registry.set(self.descriptor.key, val)

    def _on_minus(self):
        current = self.registry.get(self.descriptor.key)
        new_val = self.descriptor.dtype(
            max(self.descriptor.min_val, current - self.descriptor.step)
        )
        self.registry.set(self.descriptor.key, new_val)

    def _on_plus(self):
        current = self.registry.get(self.descriptor.key)
        new_val = self.descriptor.dtype(
            min(self.descriptor.max_val, current + self.descriptor.step)
        )
        self.registry.set(self.descriptor.key, new_val)

    def _on_registry_changed(self, val):
        self._set_display(val)
