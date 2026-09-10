from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderCapability:
    provider: str
    capability: str
    enabled: bool = True
    free_eligible: bool = True
    priority: int = 100


class ProviderRegistry:
    def __init__(self):
        self._items = []

    def register(self, item):
        self._items.append(item)

    def eligible(self, capability, free_only=True):
        return sorted(
            [
                item for item in self._items
                if item.enabled
                and item.capability == capability
                and (not free_only or item.free_eligible)
            ],
            key=lambda item: item.priority,
        )

    def best(self, capability, free_only=True):
        items = self.eligible(capability, free_only)
        return items[0] if items else None

    def snapshot(self):
        return tuple(self._items)
