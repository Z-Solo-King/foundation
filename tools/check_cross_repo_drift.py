#!/usr/bin/env python3
"""Validate the public Foundation/Operations family contract without private imports."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


DRIFT_CONTRACT_VERSION = "cross-repo-drift/v1"

EXPECTED = {
    "foundation": {
        "role": "public-contracts",
        "promotion_authority": False,
        "trust_authority": False,
        "private_secrets": False,
        "resource_governance": "operations",
    },
    "operations": {
        "role": "protected-authority",
        "promotion_authority": True,
        "trust_authority": True,
        "private_secrets": True,
    },
}


class DriftSeverity(StrEnum):
    INFO = "info"
    ERROR = "error"


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
        if any(
            not finding.repository.strip() or not finding.field.strip()
            for finding in self.findings
        ):
            raise ValueError("drift findings require repository and field")

    def canonical_json(self) -> str:
        self.validate()
        return json.dumps(
            {
                "schema_version": self.schema_version,
                "compatible": self.compatible,
                "findings": [
                    {
                        "severity": finding.severity.value,
                        "repository": finding.repository,
                        "field": finding.field,
                        "expected": finding.expected,
                        "actual": finding.actual,
                        "message": finding.message,
                    }
                    for finding in self.findings
                ],
            },
            sort_keys=True,
            separators=(",", ":"),
        )


def load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def compare_active_family_catalogs(
    foundation: dict[str, object],
    operations: dict[str, object],
) -> DriftReport:
    findings: list[DriftFinding] = []

    if foundation.get("family") != operations.get("family"):
        findings.append(
            DriftFinding(
                DriftSeverity.ERROR,
                "operations",
                "family",
                str(foundation.get("family")),
                str(operations.get("family")),
                "active family catalogs must declare the same family identity",
            )
        )

    for name, catalog in (("foundation", foundation), ("operations", operations)):
        if catalog.get("family_contract") != "docs/FAMILY_MEMBER.md":
            findings.append(
                DriftFinding(
                    DriftSeverity.ERROR,
                    name,
                    "family_contract",
                    "docs/FAMILY_MEMBER.md",
                    str(catalog.get("family_contract")),
                    "active family members must point to the canonical family contract",
                )
            )
        if catalog.get("family_contract_version") != "1":
            findings.append(
                DriftFinding(
                    DriftSeverity.ERROR,
                    name,
                    "family_contract_version",
                    "1",
                    str(catalog.get("family_contract_version")),
                    "active family contract version drifted",
                )
            )

    for name, expected in EXPECTED.items():
        catalog = foundation if name == "foundation" else operations
        for field, value in expected.items():
            if catalog.get(field) != value:
                findings.append(
                    DriftFinding(
                        DriftSeverity.ERROR,
                        name,
                        field,
                        str(value),
                        str(catalog.get(field)),
                        f"{name}: canonical boundary ownership drifted",
                    )
                )

    return DriftReport(
        schema_version=DRIFT_CONTRACT_VERSION,
        compatible=not findings,
        findings=tuple(findings),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--foundation", type=Path, required=True)
    parser.add_argument("--operations", type=Path, required=True)
    args = parser.parse_args()

    report = compare_active_family_catalogs(
        load(args.foundation), load(args.operations)
    )
    print(report.canonical_json())
    return 0 if report.compatible else 1


if __name__ == "__main__":
    raise SystemExit(main())
