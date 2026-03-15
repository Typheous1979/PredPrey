from .base import FitnessFunction


class PreyFitnessFunction(FitnessFunction):
    def score(self, organism, environment) -> float:
        params = environment.params
        energy_w    = params.get("fitness.prey.energy_weight")
        age_w       = params.get("fitness.prey.age_weight")
        offspring_w = params.get("fitness.prey.offspring_weight")
        return (
            energy_w    * organism.energy +
            age_w       * organism.age +
            offspring_w * organism.offspring_count
        )


class PredatorFitnessFunction(FitnessFunction):
    def score(self, organism, environment) -> float:
        params = environment.params
        kills_w  = params.get("fitness.predator.kills_weight")
        age_w    = params.get("fitness.predator.age_weight")
        energy_w = params.get("fitness.predator.energy_weight")
        return (
            kills_w  * organism.kills +
            age_w    * organism.age +
            energy_w * organism.energy
        )
