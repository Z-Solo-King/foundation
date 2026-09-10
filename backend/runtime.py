from backend.execution.capability import CapabilityState, CapabilityRegistry

registry = CapabilityRegistry()


def initialize_default_capabilities():
    for item in (
        CapabilityState("research_planning", True),
        CapabilityState("evidence_graph", True),
        CapabilityState("adaptive_acquisition", True),
        CapabilityState("artifact_generation", True),
    ):
        registry.register(item)
