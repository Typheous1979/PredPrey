from typing import Callable
from .descriptor import ParameterDescriptor


class ParameterRegistry:
    def __init__(self):
        self._descriptors: dict[str, ParameterDescriptor] = {}
        self._values: dict[str, float | int] = {}
        self._callbacks: dict[str, list[Callable]] = {}

    def register(self, descriptor: ParameterDescriptor) -> None:
        self._descriptors[descriptor.key] = descriptor
        self._values[descriptor.key] = descriptor.dtype(descriptor.default)

    def get(self, key: str) -> float | int:
        return self._values[key]

    def set(self, key: str, value) -> None:
        desc = self._descriptors[key]
        value = desc.dtype(max(desc.min_val, min(desc.max_val, value)))
        self._values[key] = value
        for cb in self._callbacks.get(key, []):
            cb(value)

    def on_change(self, key: str, callback: Callable) -> None:
        self._callbacks.setdefault(key, []).append(callback)

    def descriptors_by_group(self) -> dict[str, list[ParameterDescriptor]]:
        result: dict[str, list[ParameterDescriptor]] = {}
        for desc in self._descriptors.values():
            result.setdefault(desc.group, []).append(desc)
        return result

    def reset_to_defaults(self) -> None:
        for desc in self._descriptors.values():
            self.set(desc.key, desc.default)

    def all_descriptors(self) -> list[ParameterDescriptor]:
        return list(self._descriptors.values())
