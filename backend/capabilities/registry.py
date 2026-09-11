from .model import Capability


class CapabilityRegistry:
    def __init__(self):
        self._capabilities: dict[str, Capability] = {}

    def register(self, capability: Capability):
        self._capabilities[capability.name] = capability

    def get(self, name: str) -> Capability | None:
        return self._capabilities.get(name)

    def usable(self, name: str) -> bool:
        capability = self.get(name)
        return bool(capability and capability.usable())

    def all(self) -> list[Capability]:
        return list(self._capabilities.values())

    def snapshot(self) -> tuple[Capability, ...]:
        return tuple(self._capabilities.values())


registry = CapabilityRegistry()
registry.register(Capability("core", description="Core application runtime"))
