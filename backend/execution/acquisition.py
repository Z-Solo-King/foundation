"""Acquisition execution with source policy and budget enforcement.

Acquires observations from permitted sources within resource and policy constraints.
Records source lineage and access methods for every observation.
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from backend.intelligence.sources import Source, SourcePolicy, evaluate_source
from backend.intelligence.observations import Observation
from backend.intelligence.lineage import SourceLineage
from backend.execution.resources import ResourceBudget, ResourceError


@dataclass(frozen=True)
class AcquisitionMethod:
    """Method for acquiring source content."""
    name: str  # direct_http, public_api, feed, sitemap, embedded_data
    priority: int
    enabled: bool = True


DEFAULT_METHODS = (
    AcquisitionMethod("direct_http", 1),
    AcquisitionMethod("public_api", 2),
    AcquisitionMethod("feed", 3),
    AcquisitionMethod("sitemap", 4),
    AcquisitionMethod("embedded_data", 5),
)


def choose_method(source: Source, policy: SourcePolicy) -> AcquisitionMethod:
    """Choose acquisition method for a source.
    
    Raises:
        PermissionError: If source violates policy
        RuntimeError: If no method available
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
    """Choose method and consume request budget.
    
    Raises:
        ResourceError: If request budget exhausted
    """
    method = choose_method(source, policy)
    budget.consume_requests()
    return method


def simulate_acquire(
    source: Source,
    method: AcquisitionMethod,
    observation_id: str,
    content: str,
) -> Observation:
    """Simulate acquiring content from a source.
    
    In production, this would call HTTP, APIs, feeds, etc.
    For now, returns a test observation.
    """
    return Observation.create(observation_id, source.source_id, source.url, content)


def create_lineage(
    source: Source,
    family_id: str,
    parent_source_id: str | None = None,
) -> SourceLineage:
    """Create source lineage record."""
    lineage_type = "origin" if not parent_source_id else "derived"
    return SourceLineage(
        source_id=source.source_id,
        family_id=family_id,
        parent_source_id=parent_source_id,
        lineage_type=lineage_type,
    )
