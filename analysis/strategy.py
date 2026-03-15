"""
Spawn Strategy ABCs — Phase 2 skeleton.

Pluggable strategies that control how the world is seeded at startup.
Swap these into Environment._initialize() to run A/B experiments and
compare different creation approaches via SessionReport.

Phase 2 goals:
  - PlantStrategy      : where/how plants are placed initially
  - PredatorSpawnStrategy : how many predators, where, and with what genomes

Each concrete strategy should be self-contained: given (grid_width,
grid_height, params, rng) it returns everything the Environment needs.
Compare outcomes by running multiple sessions and calling
analysis.report.compare_sessions().
"""
import random
from abc import ABC, abstractmethod


# ---------------------------------------------------------------------------
# Abstract bases
# ---------------------------------------------------------------------------

class PlantStrategy(ABC):
    """Controls how plants are distributed across the grid at startup."""

    @abstractmethod
    def seed(
        self,
        grid_width: int,
        grid_height: int,
        density: float,
        rng: random.Random,
    ) -> list[tuple[int, int]]:
        """
        Return list of (x, y) grid cells to seed with plants.
        density is the configured plant_density parameter [0, 1].
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Short human-readable identifier used in logs and reports."""
        ...


class PredatorSpawnStrategy(ABC):
    """Controls initial predator count, positions, and genome seeding."""

    @abstractmethod
    def spawn_count(self, params) -> int:
        """How many predators to create at startup."""
        ...

    @abstractmethod
    def spawn_positions(
        self,
        count: int,
        grid_width: int,
        grid_height: int,
        rng: random.Random,
    ) -> list[tuple[float, float]]:
        """Return (x, y) float positions for each predator."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...


# ---------------------------------------------------------------------------
# TODO-P2: Concrete PlantStrategy implementations
# ---------------------------------------------------------------------------

# class UniformPlantStrategy(PlantStrategy):
#     """Current default: each cell seeded independently at 'density' probability."""
#     name = "uniform"
#
#     def seed(self, w, h, density, rng):
#         return [(x, y) for y in range(h) for x in range(w) if rng.random() < density]


# class ClusteredPlantStrategy(PlantStrategy):
#     """
#     Place plants in N gaussian clusters.
#     Tests whether prey evolve to home in on food patches rather than roam.
#     """
#     name = "clustered"
#
#     def __init__(self, n_clusters: int = 5, sigma: float = 8.0):
#         self.n_clusters = n_clusters
#         self.sigma = sigma
#
#     def seed(self, w, h, density, rng):
#         import math
#         target = int(w * h * density)
#         centres = [(rng.randint(0, w-1), rng.randint(0, h-1)) for _ in range(self.n_clusters)]
#         cells, seen = [], set()
#         while len(cells) < target:
#             cx, cy = rng.choice(centres)
#             x = int(cx + rng.gauss(0, self.sigma)) % w
#             y = int(cy + rng.gauss(0, self.sigma)) % h
#             if (x, y) not in seen:
#                 seen.add((x, y))
#                 cells.append((x, y))
#         return cells


# class GradientPlantStrategy(PlantStrategy):
#     """
#     Dense at centre, sparse at edges — creates a resource gradient.
#     Drives prey toward the centre and predators to follow.
#     """
#     name = "gradient"
#
#     def seed(self, w, h, density, rng):
#         cx, cy = w / 2, h / 2
#         max_d  = (cx ** 2 + cy ** 2) ** 0.5
#         cells  = []
#         for y in range(h):
#             for x in range(w):
#                 d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
#                 prob = density * (1.0 - d / max_d)
#                 if rng.random() < prob:
#                     cells.append((x, y))
#         return cells


# ---------------------------------------------------------------------------
# TODO-P2: Concrete PredatorSpawnStrategy implementations
# ---------------------------------------------------------------------------

# class RandomPredatorStrategy(PredatorSpawnStrategy):
#     """Current default: count from params, random positions."""
#     name = "random"
#
#     def spawn_count(self, params):
#         return int(params.get("initial_predators"))
#
#     def spawn_positions(self, count, w, h, rng):
#         return [(rng.uniform(0, w-1), rng.uniform(0, h-1)) for _ in range(count)]


# class PackPredatorStrategy(PredatorSpawnStrategy):
#     """
#     Spawn all predators in one corner.
#     Tests how quickly they disperse and whether pack hunting emerges.
#     """
#     name = "pack"
#
#     def spawn_count(self, params):
#         return int(params.get("initial_predators"))
#
#     def spawn_positions(self, count, w, h, rng):
#         return [(rng.uniform(0, w * 0.15), rng.uniform(0, h * 0.15)) for _ in range(count)]


# class SpecialistPredatorStrategy(PredatorSpawnStrategy):
#     """
#     Seed predators with pre-tuned genomes (high speed + high strength).
#     Tests how a head-start in traits affects long-term evolution.
#     Requires OrganismFactory to accept a genome override.
#     """
#     name = "specialist"
#     SPECIALIST_TRAITS = {"speed": 0.9, "strength": 0.9, "stealth": 0.5, "vision_range": 0.7}
#
#     def spawn_count(self, params):
#         return int(params.get("initial_predators"))
#
#     def spawn_positions(self, count, w, h, rng):
#         return [(rng.uniform(0, w-1), rng.uniform(0, h-1)) for _ in range(count)]
