from __future__ import annotations

from dataclasses import dataclass, field, replace
import hashlib
import json
from typing import Literal

ResearchDepth = Literal["quick", "standard", "deep"]

CANONICAL_RESULT_STATES = (
    "COMPLETED",
    "PARTIAL",
    "DEGRADED",
    "BLOCKED",
    "FAILED",
    "CANCELLED",
)


def _normalize_names(values: tuple[str, ...]) -> tuple[str, ...]:
    normalized = tuple(item.strip() for item in values)
    return tuple(sorted(normalized))


@dataclass(frozen=True)
class ResearchContract:
    question: str
    depth: ResearchDepth = "standard"
    require_citations: bool = True
    max_sources: int = 20
    max_evidence_items: int = 100
    query_category: str | None = None
    required_source_families: tuple[str, ...] = ()
    subquestions: tuple[str, ...] = ()
    required_output_scope: tuple[str, ...] = ()
    optional_output_scope: tuple[str, ...] = ()
    freshness_requirement: str | None = None
    evidence_requirement: str = "citations"
    allowed_tool_classes: tuple[str, ...] = ()
    deadline_ms: int | None = None
    execution_budget_units: int | None = None
    privacy_policy: str = "public_safe"
    publication_policy: str = "public_safe"
    expected_result_states: tuple[str, ...] = CANONICAL_RESULT_STATES
    contract_revision: str = "research-contract/v1"
    policy_version: str = "foundation-policy/v1"

    def validate(self) -> None:
        if not self.question.strip():
            raise ValueError("question must not be empty")
        if self.max_sources < 1:
            raise ValueError("max_sources must be positive")
        if self.max_evidence_items < 1:
            raise ValueError("max_evidence_items must be positive")
        if any(not family.strip() for family in self.required_source_families):
            raise ValueError("required_source_families must contain non-empty names")
        if len(set(self.required_source_families)) != len(self.required_source_families):
            raise ValueError("required_source_families must not contain duplicates")
        if any(not item.strip() for item in self.subquestions):
            raise ValueError("subquestions must contain non-empty values")
        if len(set(item.strip().casefold() for item in self.subquestions)) != len(self.subquestions):
            raise ValueError("subquestions must not contain duplicates")
        if any(not item.strip() for item in self.required_output_scope):
            raise ValueError("required_output_scope must contain non-empty values")
        if any(not item.strip() for item in self.optional_output_scope):
            raise ValueError("optional_output_scope must contain non-empty values")
        required = {item.strip().casefold() for item in self.required_output_scope}
        optional = {item.strip().casefold() for item in self.optional_output_scope}
        if required & optional:
            raise ValueError("required_output_scope and optional_output_scope must be disjoint")
        if self.freshness_requirement is not None and not self.freshness_requirement.strip():
            raise ValueError("freshness_requirement must be non-empty when provided")
        if not self.evidence_requirement.strip():
            raise ValueError("evidence_requirement must not be empty")
        if any(not item.strip() for item in self.allowed_tool_classes):
            raise ValueError("allowed_tool_classes must contain non-empty values")
        if len(set(item.strip().casefold() for item in self.allowed_tool_classes)) != len(self.allowed_tool_classes):
            raise ValueError("allowed_tool_classes must not contain duplicates")
        if self.deadline_ms is not None and self.deadline_ms < 1:
            raise ValueError("deadline_ms must be positive when provided")
        if self.execution_budget_units is not None and self.execution_budget_units < 1:
            raise ValueError("execution_budget_units must be positive when provided")
        if not self.privacy_policy.strip():
            raise ValueError("privacy_policy must not be empty")
        if not self.publication_policy.strip():
            raise ValueError("publication_policy must not be empty")
        if not self.expected_result_states:
            raise ValueError("expected_result_states must not be empty")
        if any(state not in CANONICAL_RESULT_STATES for state in self.expected_result_states):
            raise ValueError("expected_result_states contains an unsupported state")
        if not self.contract_revision.strip():
            raise ValueError("contract_revision must not be empty")
        if not self.policy_version.strip():
            raise ValueError("policy_version must not be empty")

    def canonical_payload(self) -> dict[str, object]:
        self.validate()
        return {
            "question": " ".join(self.question.split()),
            "depth": self.depth,
            "require_citations": self.require_citations,
            "max_sources": self.max_sources,
            "max_evidence_items": self.max_evidence_items,
            "query_category": (self.query_category or "").strip(),
            "required_source_families": list(_normalize_names(self.required_source_families)),
            "subquestions": list(_normalize_names(self.subquestions)),
            "required_output_scope": list(_normalize_names(self.required_output_scope)),
            "optional_output_scope": list(_normalize_names(self.optional_output_scope)),
            "freshness_requirement": (self.freshness_requirement or "").strip(),
            "evidence_requirement": self.evidence_requirement.strip(),
            "allowed_tool_classes": list(_normalize_names(self.allowed_tool_classes)),
            "deadline_ms": self.deadline_ms,
            "execution_budget_units": self.execution_budget_units,
            "privacy_policy": self.privacy_policy.strip(),
            "publication_policy": self.publication_policy.strip(),
            "expected_result_states": list(sorted(set(self.expected_result_states))),
            "contract_revision": self.contract_revision.strip(),
            "policy_version": self.policy_version.strip(),
        }

    @property
    def contract_fingerprint(self) -> str:
        payload = json.dumps(self.canonical_payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def derive_child(
        self,
        *,
        max_sources: int | None = None,
        max_evidence_items: int | None = None,
        deadline_ms: int | None = None,
        execution_budget_units: int | None = None,
    ) -> "ResearchContract":
        child = replace(
            self,
            max_sources=self.max_sources if max_sources is None else max_sources,
            max_evidence_items=self.max_evidence_items if max_evidence_items is None else max_evidence_items,
            deadline_ms=self.deadline_ms if deadline_ms is None else deadline_ms,
            execution_budget_units=self.execution_budget_units if execution_budget_units is None else execution_budget_units,
        )
        if child.max_sources > self.max_sources:
            raise ValueError("child contract cannot expand max_sources")
        if child.max_evidence_items > self.max_evidence_items:
            raise ValueError("child contract cannot expand max_evidence_items")
        if self.deadline_ms is not None and (child.deadline_ms is None or child.deadline_ms > self.deadline_ms):
            raise ValueError("child contract cannot relax the parent deadline")
        if self.execution_budget_units is not None and (child.execution_budget_units is None or child.execution_budget_units > self.execution_budget_units):
            raise ValueError("child contract cannot expand the parent execution budget")
        child.validate()
        return child

    def ensure_compatible(self, other: "ResearchContract") -> None:
        if self.contract_revision != other.contract_revision or self.policy_version != other.policy_version:
            raise ValueError("research contracts use incompatible revision or policy versions")


@dataclass(frozen=True)
class ResearchPlan:
    question: str
    stages: tuple[str, ...]
    source_budget: int
    evidence_budget: int
    metadata: dict[str, str] = field(default_factory=dict)
