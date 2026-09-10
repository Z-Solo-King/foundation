from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityState:
    name: str
    enabled: bool
    free_eligible: bool = True
    daily_limit: int | None = None
    used_today: int = 0

    @property
    def remaining_today(self) -> int | None:
        return None if self.daily_limit is None else max(0, self.daily_limit - self.used_today)

    def usable(self) -> bool:
        r = self.remaining_today
        return self.enabled and self.free_eligible and (r is None or r > 0)


class CapabilityRegistry:
    def __init__(self):
        self._items = {}

    def register(self, state: CapabilityState):
        self._items[state.name] = state

    def usable(self, name: str) -> bool:
        x = self._items.get(name)
        return bool(x and x.usable())
