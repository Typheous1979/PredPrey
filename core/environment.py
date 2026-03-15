import random
from core.entities import Prey, Predator, Plant, Position, Organism
from core.snapshot import SimulationSnapshot, AgentState
from core.events import EventBus, EventType, Event
from params.registry import ParameterRegistry
from simulation.behaviors import FleeBehavior, HuntBehavior, distance
from simulation.factory import OrganismFactory
from genetics.standard_engine import StandardGAEngine
from genetics.fitness import PreyFitnessFunction, PredatorFitnessFunction
from genetics.selection import tournament_selection

EAT_RADIUS = 1.5


class Environment:
    def __init__(
        self,
        params: ParameterRegistry,
        rng: random.Random = None,
        event_bus: EventBus = None,
    ):
        self.params = params
        self.rng = rng or random.Random(int(params.get("simulation.seed")))
        self.event_bus = event_bus or EventBus()
        self.tick_count = 0

        self.width: int = 0
        self.height: int = 0

        self.prey: dict[str, Prey] = {}
        self.predators: dict[str, Predator] = {}
        self.plants: dict[tuple, Plant] = {}

        self._factory = OrganismFactory(self.rng)
        self._ga = StandardGAEngine(self.rng)
        self._prey_fitness = PreyFitnessFunction()
        self._pred_fitness = PredatorFitnessFunction()
        self._flee = FleeBehavior()
        self._hunt = HuntBehavior()

        self._regrowth_counter = 0
        self._history: list[tuple[int, int, int]] = []   # (prey, preds, plants)

        self._initialize()

    # ------------------------------------------------------------------
    # Setup / reset
    # ------------------------------------------------------------------

    def _initialize(self):
        self.width  = int(self.params.get("grid_width"))
        self.height = int(self.params.get("grid_height"))
        self.prey.clear()
        self.predators.clear()
        self.plants.clear()
        self.tick_count = 0
        self._regrowth_counter = 0
        self._history.clear()

        density      = self.params.get("plant_density")
        plant_energy = self.params.get("plant_energy")
        for y in range(self.height):
            for x in range(self.width):
                if self.rng.random() < density:
                    self.plants[(x, y)] = Plant(x=x, y=y, energy=plant_energy)

        for _ in range(int(self.params.get("initial_prey"))):
            x = self.rng.uniform(0, self.width - 1)
            y = self.rng.uniform(0, self.height - 1)
            p = self._factory.create_prey(x, y)
            self.prey[p.id] = p

        for _ in range(int(self.params.get("initial_predators"))):
            x = self.rng.uniform(0, self.width - 1)
            y = self.rng.uniform(0, self.height - 1)
            p = self._factory.create_predator(x, y)
            self.predators[p.id] = p

    def reset(self):
        self._initialize()

    def add_organism(self, organism: Organism) -> None:
        if isinstance(organism, Prey):
            self.prey[organism.id] = organism
        elif isinstance(organism, Predator):
            self.predators[organism.id] = organism

    def get_neighbors(self, pos: Position, radius: float) -> list:
        result = []
        for o in list(self.prey.values()) + list(self.predators.values()):
            if distance(pos.x, pos.y, o.position.x, o.position.y) <= radius:
                result.append(o)
        return result

    # ------------------------------------------------------------------
    # Tick
    # ------------------------------------------------------------------

    def tick(self) -> SimulationSnapshot:
        self.tick_count += 1

        self._move_prey()
        self._move_predators()
        self._prey_eat_plants()
        self._predators_eat_prey()
        self._apply_metabolism()
        self._age_organisms()
        self._reap_dead()
        self._reproduce_prey()
        self._reproduce_predators()
        self._regrow_plants()

        alive_plants = sum(1 for p in self.plants.values() if p.alive)
        self._history.append((len(self.prey), len(self.predators), alive_plants))
        if len(self._history) > 1000:
            self._history = self._history[-1000:]

        return self.snapshot()

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------

    def _move_prey(self):
        for prey in self.prey.values():
            if not prey.alive:
                continue
            nx, ny = self._flee.execute(prey, self, self.rng)
            prey.position.x = nx
            prey.position.y = ny

    def _move_predators(self):
        for pred in self.predators.values():
            if not pred.alive:
                continue
            nx, ny = self._hunt.execute(pred, self, self.rng)
            pred.position.x = nx
            pred.position.y = ny

    # ------------------------------------------------------------------
    # Feeding
    # ------------------------------------------------------------------

    def _prey_eat_plants(self):
        plant_energy = self.params.get("plant_energy")
        for prey in self.prey.values():
            if not prey.alive:
                continue
            cell = (int(prey.position.x), int(prey.position.y))
            plant = self.plants.get(cell)
            if plant and plant.alive:
                prey.energy += plant_energy
                plant.alive = False
                self.event_bus.publish(Event(EventType.PREY_ATE_PLANT, {"prey_id": prey.id}))

    def _predators_eat_prey(self):
        prey_to_kill: set[str] = set()
        for pred in self.predators.values():
            if not pred.alive:
                continue
            for prey in self.prey.values():
                if not prey.alive or prey.id in prey_to_kill:
                    continue
                d = distance(pred.position.x, pred.position.y, prey.position.x, prey.position.y)
                if d >= EAT_RADIUS:
                    continue
                # Stochastic catch: depends on strength, size, camouflage, stealth
                strength   = 1.0 + pred.genome.traits.get("strength", 0.5)
                size       = 0.5 + prey.genome.traits.get("size", 0.5)
                camouflage = prey.genome.traits.get("camouflage", 0.0)
                stealth    = pred.genome.traits.get("stealth", 0.0)
                catch_prob = min(1.0, (strength / (strength + size)) * (1.0 - camouflage * 0.5) * (1.0 + stealth * 0.3))
                if self.rng.random() < catch_prob:
                    pred.energy += prey.energy * 0.7
                    pred.kills  += 1
                    prey_to_kill.add(prey.id)
                    self.event_bus.publish(Event(EventType.PREDATOR_ATE_PREY, {
                        "predator_id": pred.id, "prey_id": prey.id,
                    }))
        for pid in prey_to_kill:
            self.prey[pid].alive = False

    # ------------------------------------------------------------------
    # Metabolism / aging / death
    # ------------------------------------------------------------------

    def _apply_metabolism(self):
        for prey in self.prey.values():
            if not prey.alive:
                continue
            drain = 1.0 + prey.genome.traits.get("metabolism", 0.5) * 2.0
            drain += prey.genome.traits.get("size", 0.5) * 0.5
            prey.energy -= drain

        for pred in self.predators.values():
            if not pred.alive:
                continue
            drain = 1.5 + pred.genome.traits.get("metabolism", 0.5) * 2.5
            drain += pred.genome.traits.get("strength", 0.5) * 0.5
            pred.energy -= drain

    def _age_organisms(self):
        for org in list(self.prey.values()) + list(self.predators.values()):
            if not org.alive:
                continue
            org.age += 1
            max_age = 200 + org.genome.traits.get("lifespan_factor", 0.5) * 300
            if org.age > max_age:
                org.alive = False

    def _reap_dead(self):
        dead_prey = [oid for oid, o in self.prey.items() if not o.alive or o.energy <= 0]
        for oid in dead_prey:
            self.event_bus.publish(Event(EventType.PREY_DIED, {"prey_id": oid}))
            del self.prey[oid]

        dead_preds = [oid for oid, o in self.predators.items() if not o.alive or o.energy <= 0]
        for oid in dead_preds:
            self.event_bus.publish(Event(EventType.PREDATOR_DIED, {"predator_id": oid}))
            del self.predators[oid]

    # ------------------------------------------------------------------
    # Reproduction
    # ------------------------------------------------------------------

    def _reproduce_prey(self):
        max_prey = int(self.params.get("max_prey"))
        prey_list = list(self.prey.values())
        if len(prey_list) < 2 or len(prey_list) >= max_prey:
            return

        thresh = self.params.get("prey.reproduction_energy_thresh")
        cost   = self.params.get("prey.reproduction_cost")
        params_dict = {
            "crossover_rate":    self.params.get("prey.crossover_rate"),
            "mutation_rate":     self.params.get("prey.mutation_rate"),
            "mutation_strength": self.params.get("prey.mutation_strength"),
            "reproduction_cost": cost,
        }

        scores = [self._prey_fitness.score(p, self) for p in prey_list]
        min_s = min(scores)
        if min_s < 0:
            scores = [s - min_s for s in scores]

        new_prey: list[Prey] = []
        for prey in prey_list:
            if len(self.prey) + len(new_prey) >= max_prey:
                break
            if prey.energy < thresh:
                continue
            k = min(3, len(prey_list))
            mate = tournament_selection(prey_list, scores, k=k, rng=self.rng)
            # avoid self-mating when possible
            if mate.id == prey.id and len(prey_list) > 1:
                mate = tournament_selection(prey_list, scores, k=k, rng=self.rng)
            child = self._ga.reproduce(prey, mate, params_dict)
            child.position.x = max(0.0, min(self.width  - 1, child.position.x))
            child.position.y = max(0.0, min(self.height - 1, child.position.y))
            child.energy = cost
            prey.energy -= cost
            prey.offspring_count += 1
            new_prey.append(child)
            self.event_bus.publish(Event(EventType.PREY_BORN, {"prey_id": child.id}))

        for child in new_prey:
            self.prey[child.id] = child

    def _reproduce_predators(self):
        max_preds = int(self.params.get("max_predators"))
        pred_list = list(self.predators.values())
        if len(pred_list) < 2 or len(pred_list) >= max_preds:
            return

        thresh = self.params.get("predator.reproduction_energy_thresh")
        cost   = self.params.get("predator.reproduction_cost")
        params_dict = {
            "crossover_rate":    self.params.get("predator.crossover_rate"),
            "mutation_rate":     self.params.get("predator.mutation_rate"),
            "mutation_strength": self.params.get("predator.mutation_strength"),
            "reproduction_cost": cost,
        }

        scores = [self._pred_fitness.score(p, self) for p in pred_list]
        min_s = min(scores)
        if min_s < 0:
            scores = [s - min_s for s in scores]

        new_preds: list[Predator] = []
        for pred in pred_list:
            if len(self.predators) + len(new_preds) >= max_preds:
                break
            if pred.energy < thresh:
                continue
            k = min(3, len(pred_list))
            mate = tournament_selection(pred_list, scores, k=k, rng=self.rng)
            if mate.id == pred.id and len(pred_list) > 1:
                mate = tournament_selection(pred_list, scores, k=k, rng=self.rng)
            child = self._ga.reproduce(pred, mate, params_dict)
            child.position.x = max(0.0, min(self.width  - 1, child.position.x))
            child.position.y = max(0.0, min(self.height - 1, child.position.y))
            child.energy = cost
            pred.energy -= cost
            pred.offspring_count += 1
            new_preds.append(child)
            self.event_bus.publish(Event(EventType.PREDATOR_BORN, {"predator_id": child.id}))

        for child in new_preds:
            self.predators[child.id] = child

    # ------------------------------------------------------------------
    # Plant regrowth
    # ------------------------------------------------------------------

    def _regrow_plants(self):
        self._regrowth_counter += 1
        regrowth_ticks = int(self.params.get("plant_regrowth_ticks"))
        if self._regrowth_counter < regrowth_ticks:
            return
        self._regrowth_counter = 0
        plant_energy = self.params.get("plant_energy")
        for plant in self.plants.values():
            if not plant.alive and self.rng.random() < 0.3:
                plant.alive  = True
                plant.energy = plant_energy

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------

    def snapshot(self) -> SimulationSnapshot:
        prey_states = [
            AgentState(
                id=p.id, x=p.position.x, y=p.position.y,
                energy=p.energy, age=p.age, kind="prey",
                traits=dict(p.genome.traits),
            )
            for p in self.prey.values()
        ]
        pred_states = [
            AgentState(
                id=p.id, x=p.position.x, y=p.position.y,
                energy=p.energy, age=p.age, kind="predator",
                traits=dict(p.genome.traits),
            )
            for p in self.predators.values()
        ]
        plant_pos = [(pl.x, pl.y) for pl in self.plants.values() if pl.alive]

        return SimulationSnapshot(
            tick=self.tick_count,
            prey_states=prey_states,
            predator_states=pred_states,
            plant_positions=plant_pos,
            grid_width=self.width,
            grid_height=self.height,
            prey_count=len(self.prey),
            predator_count=len(self.predators),
            plant_count=len(plant_pos),
            stats={"history": list(self._history[-200:])},
        )
