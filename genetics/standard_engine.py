import random
from .base import GeneticAlgorithmEngine, FitnessFunction
from .selection import tournament_selection
from core.genome import uniform_crossover, mutate
from core.entities import Prey, Predator, Position


class StandardGAEngine(GeneticAlgorithmEngine):
    def __init__(self, rng: random.Random = None):
        self.rng = rng or random.Random()

    def select_parents(
        self,
        population: list,
        fitness_fn: FitnessFunction,
        environment=None,
    ) -> tuple:
        if len(population) < 2:
            return None, None
        scores = [fitness_fn.score(o, environment) for o in population]
        min_score = min(scores)
        if min_score < 0:
            scores = [s - min_score for s in scores]
        k = min(3, len(population))
        a = tournament_selection(population, scores, k=k, rng=self.rng)
        b = tournament_selection(population, scores, k=k, rng=self.rng)
        return a, b

    def reproduce(self, parent_a, parent_b, params: dict) -> object:
        crossover_rate   = params.get("crossover_rate", 0.7)
        mutation_rate    = params.get("mutation_rate", 0.05)
        mutation_strength = params.get("mutation_strength", 0.1)
        cost             = params.get("reproduction_cost", 30.0)

        if self.rng.random() < crossover_rate:
            child_genome = uniform_crossover(parent_a.genome, parent_b.genome, self.rng)
        else:
            child_genome = parent_a.genome if self.rng.random() < 0.5 else parent_b.genome

        child_genome = mutate(child_genome, mutation_rate, mutation_strength, self.rng)

        dx = self.rng.uniform(-2, 2)
        dy = self.rng.uniform(-2, 2)
        pos = Position(parent_a.position.x + dx, parent_a.position.y + dy)

        OrganismClass = type(parent_a)
        child = OrganismClass(
            id=OrganismClass.make_id(),
            position=pos,
            genome=child_genome,
            energy=cost,
        )
        return child

    def should_reproduce(self, organism, params: dict) -> bool:
        thresh = params.get("reproduction_energy_thresh", 60.0)
        return organism.energy >= thresh
