from .descriptor import ParameterDescriptor
from .registry import ParameterRegistry


def build_default_registry() -> ParameterRegistry:
    registry = ParameterRegistry()

    params = [
        # Environment
        ParameterDescriptor("grid_width",  "Grid Width",  100, 20, 300, 10, "Environment",
            "Width of the simulation world in grid cells. Each cell can hold one plant. "
            "Larger grids give agents more space to roam and reduce crowding, but increase "
            "CPU cost per tick. Pairs with Grid Height to set the total world area.",
            int),
        ParameterDescriptor("grid_height", "Grid Height", 100, 20, 300, 10, "Environment",
            "Height of the simulation world in grid cells. Each cell can hold one plant. "
            "Larger grids give agents more space to roam and reduce crowding, but increase "
            "CPU cost per tick. Pairs with Grid Width to set the total world area.",
            int),
        ParameterDescriptor("plant_density", "Plant Density", 0.2, 0.0, 1.0, 0.01, "Environment",
            "Fraction of grid cells seeded with a plant at startup. 0.2 means roughly 20% of "
            "cells start with food. Higher density means prey find food easily and populations "
            "can grow large; lower density creates scarcity that limits prey numbers and "
            "indirectly starves predators. Does not affect regrowth rate after plants are eaten."),
        ParameterDescriptor("plant_regrowth_ticks", "Plant Regrowth Ticks", 10, 1, 200, 1, "Environment",
            "Number of simulation ticks between each plant regrowth pass. Every regrowth pass, "
            "each dead plant cell has a 30% chance of coming back to life. Lower values mean "
            "food regenerates quickly, supporting larger and more stable prey populations. "
            "Higher values create boom-bust food cycles that drive prey population oscillations.",
            int),
        ParameterDescriptor("plant_energy", "Plant Energy", 20.0, 1.0, 100.0, 1.0, "Environment",
            "How much energy a prey agent gains from eating one plant. Each prey loses roughly "
            "1.5–3.0 energy per tick to metabolism, so a value of 20 gives about 7–13 ticks of "
            "survival per meal. Higher values let prey reproduce more easily and support denser "
            "populations; lower values mean prey must eat more often or starve."),

        # Population
        ParameterDescriptor("initial_prey", "Initial Prey", 50, 1, 500, 1, "Population",
            "Number of prey agents placed on the grid when the simulation starts (or resets). "
            "They are positioned randomly with random genomes. Too few risks early extinction "
            "before the population stabilises; too many can crash plant food supply immediately.",
            int),
        ParameterDescriptor("initial_predators", "Initial Predators", 10, 1, 200, 1, "Population",
            "Number of predator agents placed on the grid at startup. Too few predators and "
            "prey will overpopulate; too many will wipe out prey before the ecosystem stabilises. "
            "A ratio of roughly 1 predator per 5–10 prey is a good starting point.",
            int),
        ParameterDescriptor("max_prey", "Max Prey", 1000, 10, 10000, 10, "Population",
            "Hard ceiling on the total prey population. Reproduction is blocked once this limit "
            "is reached, regardless of individual energy levels. Acts as a carrying-capacity "
            "guardrail. Raise this to allow larger booms; lower it to keep the simulation "
            "computationally light. Note: very large populations slow down each tick.",
            int),
        ParameterDescriptor("max_predators", "Max Predators", 300, 5, 5000, 5, "Population",
            "Hard ceiling on the total predator population. Reproduction is blocked once this "
            "limit is reached. Predators have higher energy costs than prey, so they naturally "
            "self-limit below this cap most of the time. Raise it to allow predator surges "
            "during prey booms.",
            int),

        # Genetics - Prey
        ParameterDescriptor("prey.mutation_rate", "Prey Mutation Rate", 0.05, 0.0, 1.0, 0.01,
            "Genetics - Prey",
            "Probability that any individual gene in a prey offspring's genome is randomly "
            "perturbed at birth. A rate of 0.05 means each of the ~8 prey traits has a 5% "
            "chance of mutating per reproduction event. Higher rates accelerate evolution but "
            "introduce more noise; 0.0 means offspring are pure clones or crossovers with no "
            "new variation."),
        ParameterDescriptor("prey.mutation_strength", "Prey Mutation Strength", 0.1, 0.0, 1.0, 0.01,
            "Genetics - Prey",
            "Controls how large a mutation step is when a gene does mutate. Internally this is "
            "the standard deviation (sigma) of a Gaussian perturbation applied to the gene value "
            "(which lives in [0, 1]). A value of 0.1 means mutations are small and incremental; "
            "1.0 means a mutated gene can jump almost anywhere in its range in one generation."),
        ParameterDescriptor("prey.crossover_rate", "Prey Crossover Rate", 0.7, 0.0, 1.0, 0.01,
            "Genetics - Prey",
            "Probability that two parent genomes are recombined (uniform crossover) to produce "
            "a child, versus simply copying one parent. At 0.7, 70% of births mix genes from "
            "both parents; the remaining 30% are clones of one parent (before mutation). Higher "
            "crossover promotes mixing of successful traits; lower crossover preserves successful "
            "individuals more intact."),
        ParameterDescriptor("prey.reproduction_energy_thresh", "Prey Reproduction Energy",
            60.0, 10.0, 200.0, 5.0, "Genetics - Prey",
            "Minimum energy a prey agent must have before it is eligible to reproduce. If a prey "
            "is below this threshold it will not attempt to find a mate that tick. Since a prey "
            "starts each tick losing metabolism energy (1.5–3 units), this threshold determines "
            "how well-fed prey must be to breed. Raise it to make reproduction harder and slow "
            "population growth; lower it to allow hungry prey to still reproduce."),
        ParameterDescriptor("prey.reproduction_cost", "Prey Reproduction Cost", 30.0, 5.0, 100.0, 5.0,
            "Genetics - Prey",
            "Energy deducted from a prey parent when it reproduces, and also given to the "
            "newborn as its starting energy. This represents the biological cost of producing "
            "offspring. If the cost is close to the reproduction threshold, parents will "
            "reproduce infrequently and tire quickly after doing so. Lower costs mean rapid "
            "population bursts; higher costs slow reproduction and favour energy hoarders."),

        # Genetics - Predators
        ParameterDescriptor("predator.mutation_rate", "Predator Mutation Rate", 0.05, 0.0, 1.0, 0.01,
            "Genetics - Predators",
            "Probability that any individual gene in a predator offspring's genome is randomly "
            "perturbed at birth. Works identically to Prey Mutation Rate but applies to "
            "predators. Predator genomes include traits like speed, strength, stealth, and "
            "vision range. Higher rates drive faster predator adaptation to the current prey "
            "population."),
        ParameterDescriptor("predator.mutation_strength", "Predator Mutation Strength", 0.1, 0.0, 1.0, 0.01,
            "Genetics - Predators",
            "Controls the step size when a predator gene mutates — the standard deviation of "
            "the Gaussian noise applied to that gene. Works identically to Prey Mutation "
            "Strength but for predators. Smaller values produce gradual trait drift; larger "
            "values allow dramatic one-generation leaps in a trait."),
        ParameterDescriptor("predator.crossover_rate", "Predator Crossover Rate", 0.7, 0.0, 1.0, 0.01,
            "Genetics - Predators",
            "Probability that two predator parents exchange genes (uniform crossover) rather "
            "than one parent being cloned. Works identically to Prey Crossover Rate but for "
            "predators. Crossover lets successful hunting traits from different lineages combine "
            "into a single offspring."),
        ParameterDescriptor("predator.reproduction_energy_thresh", "Predator Reproduction Energy",
            80.0, 10.0, 200.0, 5.0, "Genetics - Predators",
            "Minimum energy a predator must have to attempt reproduction. Predators have a "
            "higher baseline metabolism than prey (1.5–4 units/tick), so they need more food "
            "before breeding. Raising this makes predators harder to breed, dampening population "
            "spikes after a successful hunt; lowering it lets predators reproduce on a lighter "
            "diet."),
        ParameterDescriptor("predator.reproduction_cost", "Predator Reproduction Cost",
            40.0, 5.0, 100.0, 5.0, "Genetics - Predators",
            "Energy deducted from a predator parent when it reproduces, and given to the newborn "
            "as starting energy. Higher costs mean only well-fed predators can afford offspring, "
            "naturally regulating the predator population. Lower costs risk a predator explosion "
            "that can drive prey to extinction."),

        # Fitness - Prey
        ParameterDescriptor("fitness.prey.energy_weight", "Prey Energy Weight", 1.0, 0.0, 5.0, 0.1,
            "Fitness - Prey",
            "How much a prey agent's current energy level contributes to its tournament fitness "
            "score used during mate selection. A higher weight means well-fed individuals are "
            "much more likely to be chosen as parents, evolving efficient foragers. Set to 0 to "
            "make energy irrelevant to mate selection."),
        ParameterDescriptor("fitness.prey.age_weight", "Prey Age Weight", 0.5, 0.0, 5.0, 0.1,
            "Fitness - Prey",
            "How much a prey agent's age contributes to its fitness score for mate selection. "
            "Older prey have survived longer — predator encounters, starvation, and age — so "
            "age is a proxy for overall survival ability. Higher weight means long-lived "
            "individuals dominate reproduction, evolving hardier genomes."),
        ParameterDescriptor("fitness.prey.offspring_weight", "Prey Offspring Weight", 2.0, 0.0, 5.0, 0.1,
            "Fitness - Prey",
            "How much the number of offspring a prey has already produced contributes to its "
            "fitness score. This rewards prolific breeders and creates a positive feedback: "
            "proven parents are more likely to be selected again. Higher values accelerate "
            "population growth by favouring the most reproductive individuals."),

        # Fitness - Predators
        ParameterDescriptor("fitness.predator.kills_weight", "Predator Kills Weight", 2.0, 0.0, 5.0, 0.1,
            "Fitness - Predators",
            "How much a predator's cumulative kill count contributes to its fitness score for "
            "mate selection. Higher values strongly favour successful hunters, rapidly evolving "
            "traits like speed, strength, and stealth. Set to 0 to remove hunting success from "
            "selection entirely."),
        ParameterDescriptor("fitness.predator.age_weight", "Predator Age Weight", 0.5, 0.0, 5.0, 0.1,
            "Fitness - Predators",
            "How much a predator's age contributes to its fitness score. Older predators have "
            "survived longer without starving, indicating robust genes. Works the same as Prey "
            "Age Weight but for predators. Increase it to select for long-lived, efficient "
            "hunters over lucky short-lived ones."),
        ParameterDescriptor("fitness.predator.energy_weight", "Predator Energy Weight", 1.0, 0.0, 5.0, 0.1,
            "Fitness - Predators",
            "How much a predator's current energy level contributes to its fitness score. "
            "Higher weight selects for predators that maintain high energy reserves — typically "
            "those with efficient metabolism or high hunt success. Works the same as Prey Energy "
            "Weight but for predators."),

        # Simulation
        ParameterDescriptor("simulation.ticks_per_second", "Ticks Per Second", 10, 1, 120, 1,
            "Simulation",
            "Target number of simulation ticks computed per second. One tick advances every "
            "agent's movement, feeding, metabolism, aging, death, and reproduction. Higher "
            "values run the simulation faster in real time but require more CPU. The render "
            "loop runs independently at ~60 FPS regardless of this setting, so lowering TPS "
            "does not make animation choppy — agents will just interpolate between ticks.",
            int),
        ParameterDescriptor("simulation.seed", "Random Seed", 42, 0, 99999, 1,
            "Simulation",
            "Integer seed for the random number generator. Two runs with the same seed and "
            "identical parameters will produce exactly the same sequence of events, making "
            "results reproducible. Change the seed to get a different but equally deterministic "
            "run. Takes effect on the next simulation reset.",
            int),
    ]

    for p in params:
        registry.register(p)

    return registry
