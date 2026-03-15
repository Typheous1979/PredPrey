"""
Analysis Report — Phase 2 skeleton.

Load one or more session CSV logs produced by SimulationLogger and compute
ecology metrics that describe the health and dynamics of a run.

Current (working):
  - Load session CSV into a PopulationSeries
  - Compute SessionReport: peaks, means, extinction events, stability score

Phase 2 TODOs (marked with # TODO-P2):
  - FFT-based Lotka-Volterra oscillation period detection
  - Cross-session comparison and ranking by strategy
  - Automatic parameter sensitivity sweep
"""
import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class PopulationSeries:
    """Raw time-series data loaded from a session CSV."""
    ticks:     list[int] = field(default_factory=list)
    prey:      list[int] = field(default_factory=list)
    predators: list[int] = field(default_factory=list)
    plants:    list[int] = field(default_factory=list)


@dataclass
class SessionReport:
    """Summary metrics for a single simulation run."""
    session_id:            str
    total_ticks:           int
    peak_prey:             int
    peak_predators:        int
    prey_extinctions:      int     # times prey count dropped to 0
    predator_extinctions:  int     # times predator count dropped to 0
    mean_prey:             float
    mean_predators:        float
    stability_score:       float   # coefficient of variation for prey (lower = more stable)

    # TODO-P2: oscillation_period_ticks: Optional[float] = None
    # TODO-P2: predator_prey_phase_lag:  Optional[float] = None


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_session(path: Path) -> PopulationSeries:
    """Read a session CSV into a PopulationSeries."""
    series = PopulationSeries()
    with open(path, newline="", encoding="utf-8") as f:
        # Skip comment lines written by the logger
        lines = [l for l in f if not l.startswith("#")]
    reader = csv.DictReader(lines)
    for row in reader:
        series.ticks.append(int(row["tick"]))
        series.prey.append(int(row["prey"]))
        series.predators.append(int(row["predators"]))
        series.plants.append(int(row["plants"]))
    return series


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

def analyse(series: PopulationSeries, session_id: str = "") -> SessionReport:
    """Compute a SessionReport from a PopulationSeries."""
    prey  = series.prey
    preds = series.predators
    n = len(prey)
    if n == 0:
        raise ValueError("Empty series — nothing to analyse.")

    mean_prey = sum(prey) / n
    mean_pred = sum(preds) / n
    std_prey  = (sum((x - mean_prey) ** 2 for x in prey) / n) ** 0.5
    stability = (std_prey / mean_prey) if mean_prey > 0 else float("inf")

    ext_prey = sum(1 for i in range(1, n) if prey[i] == 0 and prey[i - 1] > 0)
    ext_pred = sum(1 for i in range(1, n) if preds[i] == 0 and preds[i - 1] > 0)

    return SessionReport(
        session_id=session_id or (series.ticks[0] if series.ticks else "?"),
        total_ticks=series.ticks[-1] if series.ticks else 0,
        peak_prey=max(prey),
        peak_predators=max(preds),
        prey_extinctions=ext_prey,
        predator_extinctions=ext_pred,
        mean_prey=round(mean_prey, 1),
        mean_predators=round(mean_pred, 1),
        stability_score=round(stability, 3),
    )


def analyse_file(path: Path) -> SessionReport:
    """Convenience: load + analyse a single CSV in one call."""
    series = load_session(path)
    return analyse(series, session_id=path.stem)


# ---------------------------------------------------------------------------
# TODO-P2: Multi-session comparison
# ---------------------------------------------------------------------------

# def compare_sessions(paths: list[Path]) -> list[SessionReport]:
#     """Load multiple session CSVs and rank by stability_score (ascending)."""
#     reports = [analyse_file(p) for p in paths]
#     return sorted(reports, key=lambda r: r.stability_score)


# ---------------------------------------------------------------------------
# TODO-P2: Oscillation period detection (Lotka-Volterra cycle)
# ---------------------------------------------------------------------------

# def detect_oscillation_period(series: PopulationSeries) -> Optional[float]:
#     """
#     Use FFT on the prey time-series to find the dominant frequency.
#     Returns the period in ticks, or None if no clear cycle is found.
#
#     import numpy as np
#     signal = np.array(series.prey, dtype=float)
#     signal -= signal.mean()
#     freqs  = np.fft.rfftfreq(len(signal))
#     power  = np.abs(np.fft.rfft(signal))
#     peak   = freqs[np.argmax(power[1:]) + 1]
#     return round(1.0 / peak, 1) if peak > 0 else None
#     """
#     ...
