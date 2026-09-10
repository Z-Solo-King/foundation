from dataclasses import dataclass

from backend.intelligence.sources import Source, SourcePolicy, evaluate_source
from .resources import ResourceBudget


@dataclass(frozen=True)
class AcquisitionMethod:
    name: str
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
    if not evaluate_source(source, policy):
        raise PermissionError("source is not allowed by policy")
    for method in DEFAULT_METHODS:
        if method.enabled:
            return method
    raise RuntimeError("no acquisition method available")


def reserve_acquisition(
    source: Source,
    policy: SourcePolicy,
    budget: ResourceBudget,
) -> AcquisitionMethod:
    method = choose_method(source, policy)
    budget.consume_requests()
    return method
