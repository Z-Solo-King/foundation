from backend.capabilities.model import Capability
from backend.capabilities.registry import CapabilityRegistry

def test_registry():
    registry = CapabilityRegistry()
    capability = Capability(name="test", description="Test capability")
    registry.register(capability)
    assert registry.get("test") == capability
