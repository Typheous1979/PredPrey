import random
from dataclasses import dataclass


@dataclass
class GenomeSchema:
    traits: list[str]


PREY_SCHEMA = GenomeSchema(traits=[
    "speed", "vision_range", "flee_instinct", "metabolism",
    "fertility", "camouflage", "size", "lifespan_factor",
])

PREDATOR_SCHEMA = GenomeSchema(traits=[
    "speed", "vision_range", "hunt_aggression", "metabolism",
    "fertility", "stealth", "strength", "lifespan_factor",
])


@dataclass
class Genome:
    traits: dict[str, float]   # All values normalized to [0.0, 1.0]
    schema: GenomeSchema


def random_genome(schema: GenomeSchema, rng: random.Random) -> Genome:
    return Genome(
        traits={t: rng.random() for t in schema.traits},
        schema=schema,
    )


def uniform_crossover(a: Genome, b: Genome, rng: random.Random) -> Genome:
    new_traits = {
        trait: a.traits[trait] if rng.random() < 0.5 else b.traits[trait]
        for trait in a.schema.traits
    }
    return Genome(traits=new_traits, schema=a.schema)


def mutate(genome: Genome, rate: float, strength: float, rng: random.Random) -> Genome:
    new_traits = {}
    for trait, val in genome.traits.items():
        if rng.random() < rate:
            val = val + rng.gauss(0, strength)
            val = max(0.0, min(1.0, val))
        new_traits[trait] = val
    return Genome(traits=new_traits, schema=genome.schema)
