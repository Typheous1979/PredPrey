# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Simulation

```bash
python main.py
```

Install dependencies first if needed:
```bash
pip install -r requirements.txt
```

Quick headless smoke-test (no UI required):
```bash
python -c "
from params.defaults import build_default_registry
from core.environment import Environment
params = build_default_registry()
env = Environment(params)
for _ in range(10): snap = env.tick()
print(f'tick={snap.tick} prey={snap.prey_count} pred={snap.predator_count}')
"
```

## Architecture

### Data flow (top-level)

```
ParameterRegistry  ←──  ControlPanel (sliders + text entries)
       ↓ (reads params each tick)
  Environment.tick()
       ↓ (produces)
  SimulationSnapshot   (plain dataclass, passed via Qt signal)
       ↓ (consumed by main thread)
  SimulationView  +  PlotPanel  +  StatsDisplay
```

`SimulationRunner` (`simulation/runner.py`) is a `QThread`. It owns the `Environment`, calls `tick()` in a loop, and emits `snapshot_ready(SimulationSnapshot)`. The main thread never touches the environment directly.

### Parameter system

All tuneable values are defined once as `ParameterDescriptor` objects in `params/defaults.py`. The `ParameterRegistry` (`params/registry.py`) is the single source of truth at runtime. `ControlPanel` reads `registry.descriptors_by_group()` and auto-generates a `ParamSliderWidget` for every descriptor — adding a new `ParameterDescriptor` to `defaults.py` is all that's needed to get a live slider.

### Genome & genetics

Genome traits are floats normalized to `[0, 1]`. Phenotype conversion (e.g. speed `[0.5, 4.0]`) happens at the point of use in `simulation/behaviors.py`. Crossover and mutation are pure functions in `core/genome.py`. `StandardGAEngine` (`genetics/standard_engine.py`) wires them together with tournament selection; swap it out by implementing the `GeneticAlgorithmEngine` ABC in `genetics/base.py`.

### Environment tick order

Move prey → move predators → prey eat plants → predators eat prey → metabolism drain → age → reap dead → reproduce prey → reproduce predators → regrow plants → emit snapshot.

### Behavior strategies

`FleeBehavior` (prey): checks for predators in vision range; if none, falls through to `GrazeBehavior` (seek nearest plant). `HuntBehavior` (predator): seeks nearest prey; wanders if none in vision. All strategies receive the live `Environment` object and a `random.Random` instance — they read `environment.prey`, `environment.predators`, `environment.plants` directly.

### Key relationships to keep in mind

- `core/environment.py` imports from `simulation/behaviors.py` and `simulation/factory.py` — not the reverse.
- `genetics/fitness.py` scores organisms using `environment.params`; it receives the environment as a parameter, never imports it at module level.
- `SimulationSnapshot` is a plain dataclass (not frozen) passed across the Qt thread boundary. The UI never mutates it.
- Reset is non-destructive: `SimulationRunner.reset()` sets a flag; the runner thread calls `Environment.reset()` at the top of its next loop iteration, re-seeding from `simulation.seed`.
