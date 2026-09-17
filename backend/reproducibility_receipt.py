from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


VALID_STATES = frozenset({"NOT_ATTEMPTED", "UNKNOWN", "BLOCKED", "PARTIAL", "FAILED", "COMPLETE"})
VALID_TIERS = frozenset({"L1", "L2", "L3", "L4", "PRODUCTION"})


@dataclass(frozen=True)
class ReproducibilityReceipt:
    schema: str
    repository: str
    revision: str
    workflow_run_id: str
    suite_version: str
    configuration: str
    model_provider_mode: str
    evidence_tier: str
    fixture_id: str
    fixture_version: str
    execution_state: str
    executed_at: str
    runtime_class: str
    artifact_digest: str

    def payload(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if k != "artifact_digest"}

    def canonical_bytes(self) -> bytes:
        return json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()

    def digest(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def validate(self) -> None:
        if self.schema != "reproducibility-receipt/v1":
            raise ValueError("unsupported reproducibility receipt schema")
        required = (self.repository, self.revision, self.suite_version, self.configuration, self.model_provider_mode, self.fixture_id, self.fixture_version, self.executed_at, self.runtime_class)
        if any(not isinstance(value, str) or not value.strip() for value in required):
            raise ValueError("required reproducibility metadata is missing")
        if self.workflow_run_id is None:
            raise ValueError("workflow_run_id must be explicit, including NOT_ATTEMPTED runs")
        if self.evidence_tier not in VALID_TIERS:
            raise ValueError("invalid evidence tier")
        if self.execution_state not in VALID_STATES:
            raise ValueError("invalid execution state")
        if self.execution_state in {"NOT_ATTEMPTED", "UNKNOWN", "BLOCKED"} and self.evidence_tier == "PRODUCTION":
            raise ValueError("non-executed state cannot certify production")
        if self.artifact_digest != self.digest():
            raise ValueError("reproducibility receipt digest mismatch")


def build_receipt(**fields: Any) -> ReproducibilityReceipt:
    receipt = ReproducibilityReceipt(artifact_digest="", **fields)
    return ReproducibilityReceipt(**{**receipt.__dict__, "artifact_digest": receipt.digest()})


def compatible_baseline(current: ReproducibilityReceipt, baseline: ReproducibilityReceipt) -> bool:
    current.validate()
    baseline.validate()
    return all(getattr(current, field) == getattr(baseline, field) for field in ("repository", "suite_version", "configuration", "model_provider_mode", "fixture_id", "fixture_version", "runtime_class"))
