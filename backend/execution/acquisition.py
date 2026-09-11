"""Acquisition execution with source policy and budget enforcement.

The method declaration is owned by ``backend.sources.methods``; this module only
performs policy/budget orchestration and compatibility execution.
"""

from backend.execution.resources import ResourceBudget
from backend.intelligence.lineage import SourceLineage
from backend.intelligence.observations import Observation
from backend.intelligence.sources import Source, SourcePolicy, evaluate_source
from backend.sources.methods import AcquisitionMethod, DEFAULT_METHODS


# Compatibility exports retained for callers that imported these from execution.


def choose_method(source: Source, policy: SourcePolicy) -> AcquisitionMethod:
    """Choose the first enabled canonical acquisition method for an allowed source.

    This remains a deterministic compatibility selector. Real transport execution
    belongs to ``backend.sources`` or a private extractor implementation.
    """
    if not evaluate_source(source, policy):
        raise PermissionError(f"source {source.source_id} not allowed by policy")
    for method in DEFAULT_METHODS:
        if method.enabled:
            return method
    raise RuntimeError("no acquisition method available")


def reserve_acquisition(
    source: Source,
    policy: SourcePolicy,
    budget: ResourceBudget,
) -> AcquisitionMethod:
    """Choose a method and consume one request from the local budget."""
    method = choose_method(source, policy)
    budget.consume_requests()
    return method


def simulate_acquire(
    source: Source,
    method: AcquisitionMethod,
    observation_id: str,
    content: str,
) -> Observation:
    """Create a deterministic test observation without performing network I/O."""
    return Observation.create(observation_id, source.source_id, source.url, content)


def create_lineage(
    source: Source,
    family_id: str,
    parent_source_id: str | None = None,
) -> SourceLineage:
    """Create a source lineage record."""
    lineage_type = "origin" if not parent_source_id else "derived"
    return SourceLineage(
        source_id=source.source_id,
        family_id=family_id,
        parent_source_id=parent_source_id,
        lineage_type=lineage_type,
    )


__all__ = [
    "AcquisitionMethod",
    "DEFAULT_METHODS",
    "choose_method",
    "reserve_acquisition",
    "simulate_acquire",
    "create_lineage",
]
