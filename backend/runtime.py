from backend.capabilities.model import Capability
from backend.capabilities.registry import CapabilityRegistry

registry = CapabilityRegistry()


def initialize_default_capabilities():
    for item in (
        Capability("research_planning", description="Research planning", free_eligible=True),
        Capability("evidence_graph", description="Evidence graph", free_eligible=True),
        Capability("adaptive_acquisition", description="Adaptive acquisition", free_eligible=True),
        Capability("artifact_generation", description="Artifact generation", free_eligible=True),
    ):
        registry.register(item)
