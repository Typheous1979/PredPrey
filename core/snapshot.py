from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentState:
    id: str
    x: float
    y: float
    energy: float
    age: int
    kind: str          # "prey" | "predator"
    traits: dict[str, float]


@dataclass
class SimulationSnapshot:
    tick: int
    prey_states: list[AgentState]
    predator_states: list[AgentState]
    plant_positions: list[tuple[int, int]]
    grid_width: int
    grid_height: int
    prey_count: int
    predator_count: int
    plant_count: int
    stats: dict[str, Any] = field(default_factory=dict)
