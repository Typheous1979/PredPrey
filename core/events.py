from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Callable


class EventType(Enum):
    PREY_BORN = auto()
    PREY_DIED = auto()
    PREDATOR_BORN = auto()
    PREDATOR_DIED = auto()
    PREY_ATE_PLANT = auto()
    PREDATOR_ATE_PREY = auto()
    TICK_COMPLETE = auto()


@dataclass
class Event:
    type: EventType
    data: dict[str, Any] = field(default_factory=dict)


class EventBus:
    def __init__(self):
        self._handlers: dict[EventType, list[Callable]] = {}

    def subscribe(self, event_type: EventType, handler: Callable[["Event"], None]) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: Event) -> None:
        for handler in self._handlers.get(event.type, []):
            handler(event)

    def clear(self) -> None:
        self._handlers.clear()
