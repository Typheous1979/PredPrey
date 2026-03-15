"""
Real-time session logger.

Writes one CSV row per simulation tick to logs/session_TIMESTAMP.csv
automatically while the simulation runs. A new file is created each time
the simulation starts or resets.

CSV columns: tick, prey, predators, plants
"""
import csv
import time
from pathlib import Path

from core.snapshot import SimulationSnapshot

LOG_DIR = Path("logs")


class SimulationLogger:
    def __init__(self):
        self._file = None
        self._writer = None
        self._session_id: str | None = None
        self._current_path: Path | None = None

    # ------------------------------------------------------------------

    def start_session(self, param_notes: str = "") -> Path:
        """Open a new CSV log file. Call on simulation start or reset."""
        self._close()
        LOG_DIR.mkdir(exist_ok=True)
        self._session_id = time.strftime("%Y%m%d_%H%M%S")
        self._current_path = LOG_DIR / f"session_{self._session_id}.csv"
        self._file = open(self._current_path, "w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._file)
        if param_notes:
            self._file.write(f"# {param_notes}\n")
        self._writer.writerow(["tick", "prey", "predators", "plants"])
        self._file.flush()
        return self._current_path

    def log_tick(self, snapshot: SimulationSnapshot) -> None:
        """Append one row for this tick. Safe to call even before start_session."""
        if self._writer is None:
            return
        self._writer.writerow([
            snapshot.tick,
            snapshot.prey_count,
            snapshot.predator_count,
            snapshot.plant_count,
        ])
        if snapshot.tick % 20 == 0:
            self._file.flush()

    def end_session(self) -> None:
        """Flush and close the current log file."""
        self._close()

    @property
    def current_path(self) -> Path | None:
        return self._current_path

    # ------------------------------------------------------------------

    def _close(self):
        if self._file:
            self._file.flush()
            self._file.close()
        self._file = None
        self._writer = None
