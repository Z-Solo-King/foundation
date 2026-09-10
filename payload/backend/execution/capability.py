from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityState:
    name: str
    enabled: bool
    free_eligible: bool = True
    daily_limit: int | None = None
    used_today: int = 0

    @property
    def remaining_today(self):
        if self.daily_limit is None:
            return None
        return max(0, self.daily_limit - self.used_today)

    def usable(self):
        remaining = self.remaining_today
        return (
            self.enabled
            and self.free_eligible
            and (remaining is None or remaining > 0)
        )


class CapabilityRegistry:
    def __init__(self):
        self._items = {}

    def register(self, state):
        self._items[state.name] = state

    def get(self, name):
        return self._items.get(name)

    def usable(self, name):
        item = self.get(name)
        return bool(item and item.usable())

    def snapshot(self):
        return tuple(self._items.values())
