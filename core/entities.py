import uuid
from dataclasses import dataclass, field
from .genome import Genome


@dataclass
class Position:
    x: float
    y: float


@dataclass
class Plant:
    x: int
    y: int
    energy: float = 20.0
    alive: bool = True


@dataclass
class Organism:
    id: str
    position: Position
    genome: Genome
    energy: float
    age: int = 0
    offspring_count: int = 0
    alive: bool = True

    @staticmethod
    def make_id() -> str:
        return str(uuid.uuid4())[:8]


@dataclass
class Prey(Organism):
    pass


@dataclass
class Predator(Organism):
    kills: int = 0
