from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
from typing import Mapping


DRIFT_CONTRACT_VERSION = "cross-repo-drift/v1"

_REQUIRED_FIELDS = (
    "family",
    "family_contract",
    "family_contract_version",
    "name",
    "role",
    "trust_level",
    "determinism",
    "promotion_authority",
    "evidence_authority",
    "trust_authority",
    "private_secrets",
    "protected_boundaries",
)


class DriftSeverity(StrEnum):
    INFO = "info"
    ERROR = "error"


@dataclass(frozen=True)
class ContractCatalog:
    name: str
    revision: str
    role: str
    family: str
    family_contract_version: str
    promotion_authority: bool
    evidence_authority: str
    trust_authority: bool
    private_secrets: bool
    capabilities: Mapping[str, str]
    owners: Mapping[str, str]
    schemas: Mapping[str, str]

    def validate(self) -> None:
        if not self.name.strip() or not self.revision.strip() or not self.role.strip() or not self.family.strip():
            raise ValueError("catalog identity fields are required")
        if not self.family_contract_version.strip():
            raise ValueError("family_contract_version is required")
        if not isinstance(self.promotion_authority, bool) or not isinstance(self.trust_authority, bool) or not isinstance(self.private_secrets, bool):
            raise ValueError("authority flags must be boolean")
        for mapping, field in ((self.capabilities, "capabilities"), (self.owners, "owners"), (self.schemas, "schemas")):
            if any(not str(key).strip() or not str(value).strip() for key, value in mapping.items()):
                raise ValueError(f"{field} contains an empty key or value")


@dataclass(frozen=True)
class DriftFinding:
    severity: DriftSeverity
    repository: str
    field: str
    expected: str
    actual: str
    message: str


@dataclass(frozen=True)
class DriftReport:
    schema_version: str
    compatible: bool
    findings: tuple[DriftFinding, ...]

    def validate(self) -> None:
        if self.schema_version != DRIFT_CONTRACT_VERSION:
            raise ValueError("unsupported drift contract version")
        if any(not finding.repository.strip() or not finding.field.strip() for finding in self.findings):
            raise ValueError("drift findings require repository and field")


def catalog_from_capabilities(
    capabilities: Mapping[str, object],
    *,
    revision: str,
    owners: Mapping[str, str] | None = None,
    schemas: Mapping[str, str] | None = None,
) -> ContractCatalog:
    missing = [field for field in _REQUIRED_FIELDS if field not in capabilities]
    if missing:
        raise ValueError(f"capabilities catalog is missing required fields: {', '.join(missing)}")
    for field in ("promotion_authority", "trust_authority", "private_secrets"):
        if not isinstance(capabilities[field], bool):
            raise ValueError(f"{field} must be boolean")
    catalog = ContractCatalog(
        name=str(capabilities["name"]),
        revision=revision,
        role=str(capabilities["role"]),
        family=str(capabilities["family"]),
        family_contract_version=str(capabilities["family_contract_version"]),
        promotion_authority=capabilities["promotion_authority"],
        evidence_authority=str(capabilities["evidence_authority"]),
        trust_authority=capabilities["trust_authority"],
        private_secrets=capabilities["private_secrets"],
        capabilities={str(key): str(value) for key, value in capabilities.get("capabilities", {}).items()},
        owners={str(key): str(value) for key, value in (owners or {}).items()},
        schemas={str(key): str(value) for key, value in (schemas or {}).items()},
    )
    catalog.validate()
    return catalog


def compare_catalogs(
    baseline: ContractCatalog,
    candidate: ContractCatalog,
    *,
    required_capabilities: tuple[str, ...] = (),
) -> DriftReport:
    baseline.validate()
    candidate.validate()
    findings: list[DriftFinding] = []

    for field in ("family", "family_contract_version", "role", "promotion_authority", "evidence_authority", "trust_authority", "private_secrets"):
        expected = str(getattr(baseline, field))
        actual = str(getattr(candidate, field))
        if expected != actual:
            findings.append(
                DriftFinding(
                    DriftSeverity.ERROR,
                    candidate.name,
                    field,
                    expected,
                    actual,
                    f"{candidate.name}: {field} drifted from {baseline.name}",
                )
            )

    for capability in sorted(set(required_capabilities) | set(baseline.capabilities) | set(candidate.capabilities)):
        expected = baseline.capabilities.get(capability, "<required>" if capability in required_capabilities else "<missing>")
        actual = candidate.capabilities.get(capability, "<missing>")
        if capability in required_capabilities and capability not in candidate.capabilities:
            findings.append(
                DriftFinding(
                    DriftSeverity.ERROR,
                    candidate.name,
                    f"capability.{capability}",
                    expected,
                    "<missing>",
                    f"{candidate.name}: required capability is missing",
                )
            )
            continue
        if expected != actual:
            findings.append(
                DriftFinding(
                    DriftSeverity.ERROR,
                    candidate.name,
                    f"capability.{capability}",
                    expected,
                    actual,
                    f"{candidate.name}: capability revision drift for {capability}",
                )
            )

    for key in sorted(set(baseline.owners) | set(candidate.owners)):
        expected = baseline.owners.get(key, "<missing>")
        actual = candidate.owners.get(key, "<missing>")
        if expected != actual:
            findings.append(
                DriftFinding(
                    DriftSeverity.ERROR,
                    candidate.name,
                    f"owner.{key}",
                    expected,
                    actual,
                    f"{candidate.name}: ownership changed for {key}",
                )
            )

    for key in sorted(set(baseline.schemas) | set(candidate.schemas)):
        expected = baseline.schemas.get(key, "<missing>")
        actual = candidate.schemas.get(key, "<missing>")
        if expected != actual:
            findings.append(
                DriftFinding(
                    DriftSeverity.ERROR,
                    candidate.name,
                    f"schema.{key}",
                    expected,
                    actual,
                    f"{candidate.name}: schema revision drift for {key}",
                )
            )

    report = DriftReport(
        schema_version=DRIFT_CONTRACT_VERSION,
        compatible=not any(f.severity is DriftSeverity.ERROR for f in findings),
        findings=tuple(findings),
    )
    report.validate()
    return report


def canonical_json(report: DriftReport) -> str:
    report.validate()
    payload = {
        "schema_version": report.schema_version,
        "compatible": report.compatible,
        "findings": [
            {
                "severity": finding.severity.value,
                "repository": finding.repository,
                "field": finding.field,
                "expected": finding.expected,
                "actual": finding.actual,
                "message": finding.message,
            }
            for finding in report.findings
        ],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
