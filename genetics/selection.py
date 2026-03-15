import random


def tournament_selection(
    population: list,
    fitness_scores: list[float],
    k: int = 3,
    rng: random.Random = None,
) -> object:
    if rng is None:
        rng = random.Random()
    k = min(k, len(population))
    candidates = rng.choices(range(len(population)), k=k)
    winner_idx = max(candidates, key=lambda i: fitness_scores[i])
    return population[winner_idx]


def roulette_selection(
    population: list,
    fitness_scores: list[float],
    rng: random.Random = None,
) -> object:
    if rng is None:
        rng = random.Random()
    total = sum(fitness_scores)
    if total <= 0:
        return rng.choice(population)
    pick = rng.uniform(0, total)
    running = 0.0
    for organism, score in zip(population, fitness_scores):
        running += score
        if running >= pick:
            return organism
    return population[-1]
