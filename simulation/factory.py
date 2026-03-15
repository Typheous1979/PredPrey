import random
from core.entities import Prey, Predator, Position
from core.genome import random_genome, PREY_SCHEMA, PREDATOR_SCHEMA


class OrganismFactory:
    def __init__(self, rng: random.Random = None):
        self.rng = rng or random.Random()

    def create_prey(self, x: float, y: float, energy: float = 50.0) -> Prey:
        return Prey(
            id=Prey.make_id(),
            position=Position(x, y),
            genome=random_genome(PREY_SCHEMA, self.rng),
            energy=energy,
        )

    def create_predator(self, x: float, y: float, energy: float = 70.0) -> Predator:
        return Predator(
            id=Predator.make_id(),
            position=Position(x, y),
            genome=random_genome(PREDATOR_SCHEMA, self.rng),
            energy=energy,
        )
