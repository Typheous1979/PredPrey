"""
SQLite database interface for persisting simulation run history.

Database file: predprey.db (project root)

Schema
------
runs  — one row per saved run (metadata + summary stats)
ticks — one row per tick for each run (full time-series)

Usage
-----
    from analysis.database import SimulationDB
    db = SimulationDB()
    run_id = db.save_run(history, notes="high predator pressure")
    entries = db.list_runs()          # [(id, label), ...]
    series  = db.load_run(run_id)     # list of (tick, prey, pred, plants)
    db.delete_run(run_id)
"""
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("predprey.db")


class SimulationDB:
    def __init__(self, path: Path = DB_PATH):
        self._path = path
        self._ensure_tables()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _ensure_tables(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS runs (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    saved_at      TEXT    NOT NULL,
                    total_ticks   INTEGER NOT NULL DEFAULT 0,
                    peak_prey     INTEGER NOT NULL DEFAULT 0,
                    peak_predators INTEGER NOT NULL DEFAULT 0,
                    notes         TEXT
                );

                CREATE TABLE IF NOT EXISTS ticks (
                    run_id     INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
                    tick       INTEGER NOT NULL,
                    prey       INTEGER NOT NULL,
                    predators  INTEGER NOT NULL,
                    plants     INTEGER NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_ticks_run ON ticks(run_id);
            """)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save_run(
        self,
        history: list[tuple[int, int, int, int]],
        notes: str = "",
    ) -> int:
        """
        Persist a run to the database.

        history: list of (tick, prey, predators, plants)
        Returns the new run_id.
        """
        if not history:
            raise ValueError("Cannot save an empty run.")

        total_ticks    = history[-1][0]
        peak_prey      = max(r[1] for r in history)
        peak_predators = max(r[2] for r in history)
        saved_at       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO runs (saved_at, total_ticks, peak_prey, peak_predators, notes) "
                "VALUES (?, ?, ?, ?, ?)",
                (saved_at, total_ticks, peak_prey, peak_predators, notes or None),
            )
            run_id = cur.lastrowid
            conn.executemany(
                "INSERT INTO ticks (run_id, tick, prey, predators, plants) VALUES (?,?,?,?,?)",
                [(run_id, *row) for row in history],
            )
        return run_id

    def delete_run(self, run_id: int) -> None:
        """Delete a run and all its tick data (CASCADE handles ticks)."""
        with self._connect() as conn:
            conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def list_runs(self) -> list[tuple[int, str]]:
        """
        Return [(run_id, display_label), ...] ordered newest first.
        Label format: "Run #N — YYYY-MM-DD HH:MM  •  T ticks  •  peak prey P"
        """
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, saved_at, total_ticks, peak_prey "
                "FROM runs ORDER BY id DESC"
            ).fetchall()
        result = []
        for run_id, saved_at, total_ticks, peak_prey in rows:
            label = (
                f"Run #{run_id}  —  {saved_at}"
                f"  •  {total_ticks} ticks"
                f"  •  peak prey: {peak_prey}"
            )
            result.append((run_id, label))
        return result

    def load_run(self, run_id: int) -> list[tuple[int, int, int, int]]:
        """Return list of (tick, prey, predators, plants) for the given run."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT tick, prey, predators, plants FROM ticks "
                "WHERE run_id = ? ORDER BY tick",
                (run_id,),
            ).fetchall()
        return rows
