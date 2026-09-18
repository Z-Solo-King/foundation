from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping


@dataclass(frozen=True)
class ClaimSnapshot:
    snapshot_id: str
    claim_id: str
    text: str
    observed_at: datetime

    @classmethod
    def create(cls, snapshot_id, claim_id, text):
        return cls(snapshot_id, claim_id, text, datetime.now(timezone.utc))


def changed(previous: ClaimSnapshot, current: ClaimSnapshot) -> bool:
    return previous.claim_id == current.claim_id and previous.text != current.text


@dataclass(frozen=True)
class AnswerSnapshot:
    """Privacy-safe semantic snapshot for reproducible result comparison."""

    snapshot_id: str
    execution_identity: str
    requested_scope: tuple[str, ...]
    completed_scope: tuple[str, ...]
    claim_support: Mapping[str, str]
    freshness: Mapping[str, str]
    source_fingerprints: tuple[str, ...]
    capability_version: str
    policy_version: str
    result_digest: str
    resource_units: int = 0
    latency_ms: int = 0
    missing_scope: tuple[str, ...] = ()
    contradiction_state: Mapping[str, str] = field(default_factory=dict)
    provider_model_identity: str | None = None
    reliability_state: str | None = None

    def validate(self) -> None:
        if not self.snapshot_id.strip() or not self.execution_identity.strip():
            raise ValueError("snapshot identity is required")
        if not self.capability_version.strip() or not self.policy_version.strip():
            raise ValueError("capability and policy versions are required")
        if not self.result_digest.strip():
            raise ValueError("result_digest is required")
        if self.resource_units < 0 or self.latency_ms < 0:
            raise ValueError("resource and latency values must be non-negative")
        if self.provider_model_identity is not None and not self.provider_model_identity.strip():
            raise ValueError("provider_model_identity must be non-empty when provided")
        if self.reliability_state is not None and not self.reliability_state.strip():
            raise ValueError("reliability_state must be non-empty when provided")

    def semantic_diff(self, other: "AnswerSnapshot") -> dict[str, bool]:
        self.validate()
        other.validate()
        return {
            "scope_changed": (self.requested_scope, self.completed_scope, self.missing_scope) != (other.requested_scope, other.completed_scope, other.missing_scope),
            "claim_support_changed": dict(self.claim_support) != dict(other.claim_support),
            "freshness_changed": dict(self.freshness) != dict(other.freshness),
            "contradiction_state_changed": dict(self.contradiction_state) != dict(other.contradiction_state),
            "sources_changed": self.source_fingerprints != other.source_fingerprints,
            "capability_changed": self.capability_version != other.capability_version,
            "policy_changed": self.policy_version != other.policy_version,
            "result_changed": self.result_digest != other.result_digest,
            "resource_changed": self.resource_units != other.resource_units,
            "latency_changed": self.latency_ms != other.latency_ms,
            "provider_model_changed": self.provider_model_identity != other.provider_model_identity,
            "reliability_changed": self.reliability_state != other.reliability_state,
        }
