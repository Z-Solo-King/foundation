from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderCapability:
    provider: str
    capability: str
    enabled: bool = True
    free_eligible: bool = True
    priority: int = 100


class ProviderRegistry:
    def __init__(self) -> None:
        self._items: list[ProviderCapability] = []

    def register(self, item: ProviderCapability) -> None:
        self._items.append(item)

    def eligible(self, capability: str, free_only: bool = True) -> list[ProviderCapability]:
        items = [
            item for item in self._items
            if item.enabled
            and item.capability == capability
            and (not free_only or item.free_eligible)
        ]
        return sorted(items, key=lambda item: item.priority)

    def best(self, capability: str, free_only: bool = True) -> ProviderCapability | None:
        items = self.eligible(capability, free_only)
        return items[0] if items else None


registry = ProviderRegistry()
