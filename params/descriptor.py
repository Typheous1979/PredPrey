from dataclasses import dataclass


@dataclass
class ParameterDescriptor:
    key: str          # "prey.mutation_rate"
    label: str        # "Prey Mutation Rate"
    default: float
    min_val: float
    max_val: float
    step: float
    group: str        # "Genetics - Prey"
    tooltip: str = ""
    dtype: type = float
