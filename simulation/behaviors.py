import math
import random
from core.entities import Organism, Position


# ---------- helpers ----------------------------------------------------------

def _clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def distance(ax: float, ay: float, bx: float, by: float) -> float:
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)


def _move_toward(ox, oy, tx, ty, speed: float) -> tuple[float, float]:
    dx, dy = tx - ox, ty - oy
    d = math.sqrt(dx * dx + dy * dy) or 1e-9
    return ox + (dx / d) * speed, oy + (dy / d) * speed


def _move_away(ox, oy, tx, ty, speed: float) -> tuple[float, float]:
    dx, dy = ox - tx, oy - ty
    d = math.sqrt(dx * dx + dy * dy) or 1e-9
    return ox + (dx / d) * speed, oy + (dy / d) * speed


# Trait → phenotype mappings
def _speed(organism: Organism) -> float:
    return 0.5 + organism.genome.traits.get("speed", 0.5) * 3.5   # [0.5, 4.0]


def _vision(organism: Organism) -> float:
    return 2.0 + organism.genome.traits.get("vision_range", 0.5) * 18.0  # [2, 20]


# ---------- strategies -------------------------------------------------------

class BehaviorStrategy:
    def execute(self, organism: Organism, environment, rng: random.Random) -> tuple[float, float]:
        raise NotImplementedError


class WanderBehavior(BehaviorStrategy):
    def execute(self, organism, environment, rng):
        speed = _speed(organism)
        nx = _clamp(organism.position.x + rng.uniform(-speed, speed), 0, environment.width - 1)
        ny = _clamp(organism.position.y + rng.uniform(-speed, speed), 0, environment.height - 1)
        return nx, ny


class GrazeBehavior(BehaviorStrategy):
    """Prey: move toward nearest plant; wander if none in vision."""

    def execute(self, organism, environment, rng):
        speed  = _speed(organism)
        vision = _vision(organism)
        px, py = organism.position.x, organism.position.y

        nearest, nearest_dist = None, float("inf")
        for plant in environment.plants.values():
            if not plant.alive:
                continue
            d = distance(px, py, plant.x, plant.y)
            if d < vision and d < nearest_dist:
                nearest_dist, nearest = d, plant

        if nearest:
            nx, ny = _move_toward(px, py, nearest.x, nearest.y, speed)
        else:
            nx = px + rng.uniform(-speed, speed)
            ny = py + rng.uniform(-speed, speed)

        return _clamp(nx, 0, environment.width - 1), _clamp(ny, 0, environment.height - 1)


class FleeBehavior(BehaviorStrategy):
    """Prey: flee predators when visible; otherwise graze."""

    def __init__(self):
        self._graze = GrazeBehavior()

    def execute(self, organism, environment, rng):
        speed  = _speed(organism)
        vision = _vision(organism)
        flee   = organism.genome.traits.get("flee_instinct", 0.5)
        px, py = organism.position.x, organism.position.y

        nearest, nearest_dist = None, float("inf")
        for pred in environment.predators.values():
            if not pred.alive:
                continue
            d = distance(px, py, pred.position.x, pred.position.y)
            if d < vision and d < nearest_dist:
                nearest_dist, nearest = d, pred

        if nearest and rng.random() < flee:
            nx, ny = _move_away(px, py, nearest.position.x, nearest.position.y, speed)
            return _clamp(nx, 0, environment.width - 1), _clamp(ny, 0, environment.height - 1)

        return self._graze.execute(organism, environment, rng)


class HuntBehavior(BehaviorStrategy):
    """Predator: chase nearest prey; wander if none in vision."""

    def execute(self, organism, environment, rng):
        speed      = _speed(organism)
        vision     = _vision(organism)
        aggression = organism.genome.traits.get("hunt_aggression", 0.5)
        px, py     = organism.position.x, organism.position.y

        nearest, nearest_dist = None, float("inf")
        for prey in environment.prey.values():
            if not prey.alive:
                continue
            d = distance(px, py, prey.position.x, prey.position.y)
            if d < vision and d < nearest_dist:
                nearest_dist, nearest = d, prey

        if nearest and rng.random() < aggression:
            nx, ny = _move_toward(px, py, nearest.position.x, nearest.position.y, speed)
        else:
            nx = px + rng.uniform(-speed, speed)
            ny = py + rng.uniform(-speed, speed)

        return _clamp(nx, 0, environment.width - 1), _clamp(ny, 0, environment.height - 1)
