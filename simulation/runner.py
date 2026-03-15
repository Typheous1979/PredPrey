import time
from PyQt6.QtCore import QThread, pyqtSignal
from core.environment import Environment
from core.events import EventBus
from params.registry import ParameterRegistry


class SimulationRunner(QThread):
    snapshot_ready = pyqtSignal(object)   # emits SimulationSnapshot

    def __init__(self, params: ParameterRegistry, event_bus: EventBus = None, parent=None):
        super().__init__(parent)
        self.params = params
        self.event_bus = event_bus or EventBus()
        self._environment: Environment | None = None
        self._running = False
        self._paused = False
        self._reset_requested = False

    def run(self):
        self._environment = Environment(self.params, event_bus=self.event_bus)
        self._running = True
        target = time.perf_counter()

        while self._running:
            if self._reset_requested:
                self._environment.reset()
                self._reset_requested = False
                target = time.perf_counter()

            if not self._paused:
                snapshot = self._environment.tick()
                self.snapshot_ready.emit(snapshot)

            tps = max(1, int(self.params.get("simulation.ticks_per_second")))
            target += 1.0 / tps

            # Sleep most of the wait, then spin the final ~1 ms for precision
            remaining = target - time.perf_counter()
            if remaining > 0.002:
                time.sleep(remaining - 0.001)
            while time.perf_counter() < target:
                pass

            # Guard against spiral of death if tick() takes longer than the interval
            if time.perf_counter() - target > 0.1:
                target = time.perf_counter()

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def reset(self):
        self._reset_requested = True

    def stop_simulation(self):
        self._running = False
        self.wait(3000)
