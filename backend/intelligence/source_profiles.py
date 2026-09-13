"""Replayable source/method health state used by planning, not by policy."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .planner_models import FailureClass, SourceProfileHint


@dataclass(frozen=True)
class MethodObservation:
    method_id: str
    success: bool
    completeness: float = 0.0
    latency_ms: int = 0
    bytes_read: int = 0
    failure: FailureClass | None = None
    observed_at: str = ""


@dataclass(frozen=True)
class SourceProfile:
    source_id: str
    source_family: str
    platform_hint: str | None = None
    supported_representations: tuple[str, ...] = ()
    preferred_method: str | None = None
    pagination: str | None = None
    structured_surfaces: tuple[str, ...] = ()
    success_by_method: Mapping[str, float] = field(default_factory=dict)
    failure_by_class: Mapping[str, int] = field(default_factory=dict)
    completeness_by_method: Mapping[str, float] = field(default_factory=dict)
    health: float = 1.0
    sample_size: int = 0
    concurrency_ceiling: int = 1
    last_good_at: str | None = None
    quarantined_until: str | None = None
    version: str = "1"

    def hint(self) -> SourceProfileHint:
        failures = tuple(FailureClass(k) for k in self.failure_by_class if k in {f.value for f in FailureClass})
        return SourceProfileHint(
            source_id=self.source_id,
            supported_representations=self.supported_representations,
            preferred_method=self.preferred_method,
            pagination=self.pagination,
            known_failures=failures,
            concurrency_ceiling=self.concurrency_ceiling,
            health=self.health,
            sample_size=self.sample_size,
            last_success_at=self.last_good_at,
        )


def update_profile(profile: SourceProfile, observation: MethodObservation) -> SourceProfile:
    n = profile.sample_size + 1
    alpha = 1.0 / n
    prior_success = profile.success_by_method.get(observation.method_id, 0.5)
    prior_complete = profile.completeness_by_method.get(observation.method_id, 0.5)
    success = prior_success + alpha * ((1.0 if observation.success else 0.0) - prior_success)
    completeness = prior_complete + alpha * (max(0.0, min(1.0, observation.completeness)) - prior_complete)
    failures = dict(profile.failure_by_class)
    if observation.failure is not None:
        failures[observation.failure.value] = failures.get(observation.failure.value, 0) + 1
    success_map = dict(profile.success_by_method); success_map[observation.method_id] = success
    complete_map = dict(profile.completeness_by_method); complete_map[observation.method_id] = completeness
    health = max(0.0, min(1.0, 0.8 * profile.health + 0.2 * (1.0 if observation.success else 0.0)))
    preferred = profile.preferred_method
    if observation.success and (preferred is None or success >= success_map.get(preferred, 0.0)):
        preferred = observation.method_id
    return SourceProfile(
        source_id=profile.source_id, source_family=profile.source_family,
        platform_hint=profile.platform_hint, supported_representations=profile.supported_representations,
        preferred_method=preferred, pagination=profile.pagination, structured_surfaces=profile.structured_surfaces,
        success_by_method=success_map, failure_by_class=failures, completeness_by_method=complete_map,
        health=health, sample_size=n, concurrency_ceiling=profile.concurrency_ceiling,
        last_good_at=observation.observed_at if observation.success else profile.last_good_at,
        quarantined_until=profile.quarantined_until, version=profile.version,
    )
