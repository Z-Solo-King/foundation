#!/usr/bin/env python3
"""Validate the shared Foundation/Operations family contract without copying runtime authority."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.governance.contract_drift import (
    DRIFT_CONTRACT_VERSION,
    DriftFinding,
    DriftReport,
    DriftSeverity,
)


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
        if catalog.get("family_contract") != "docs/FAMILY_CONTRACT.json":
            findings.append(
                DriftFinding(
                    DriftSeverity.ERROR,
                    name,
                    "family_contract",
                    "docs/FAMILY_CONTRACT.json",
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

    if foundation.get("resource_governance") != "operations":
        findings.append(
            DriftFinding(
                DriftSeverity.ERROR,
                "foundation",
                "resource_governance",
                "operations",
                str(foundation.get("resource_governance")),
                "Foundation must not own protected resource governance",
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

    report = compare_active_family_catalogs(load(args.foundation), load(args.operations))
    report.validate()
    print(report.canonical_json() if hasattr(report, "canonical_json") else json.dumps({
        "schema_version": report.schema_version,
        "compatible": report.compatible,
        "findings": [
            {
                "severity": item.severity.value,
                "repository": item.repository,
                "field": item.field,
                "expected": item.expected,
                "actual": item.actual,
                "message": item.message,
            }
            for item in report.findings
        ],
    }, sort_keys=True, separators=(",", ":")))
    return 0 if report.compatible else 1


if __name__ == "__main__":
    raise SystemExit(main())
