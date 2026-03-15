from abc import ABC, abstractmethod


class FitnessFunction(ABC):
    @abstractmethod
    def score(self, organism, environment) -> float:
        ...


class GeneticAlgorithmEngine(ABC):
    @abstractmethod
    def select_parents(self, population: list, fitness_fn: FitnessFunction, environment=None) -> tuple:
        ...

    @abstractmethod
    def reproduce(self, parent_a, parent_b, params: dict) -> object:
        ...

    @abstractmethod
    def should_reproduce(self, organism, params: dict) -> bool:
        ...
