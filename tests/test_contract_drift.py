import json

import pytest

from backend.governance.contract_drift import (
    DRIFT_CONTRACT_VERSION,
    ContractCatalog,
    DriftReport,
    catalog_from_capabilities,
    canonical_json,
    compare_catalogs,
)


BASE_CAPABILITIES = {
    "family": "z-solo-king-github-family",
    "family_contract": "docs/FAMILY_MEMBER.md",
    "family_contract_version": "1",
    "name": "foundation",
    "role": "public-contracts",
    "trust_level": "public",
    "determinism": "deterministic-first",
    "network_access": ["approved-http-sources"],
    "ai_usage": ["semantic-entailment-adjudication"],
    "promotion_authority": False,
    "evidence_authority": "structural-contracts-only",
    "trust_authority": False,
    "private_secrets": False,
    "protected_boundaries": ["privacy", "security"],
}


def catalog(**changes):
    payload = dict(BASE_CAPABILITIES)
    payload.update(changes)
    return catalog_from_capabilities(
        payload,
        revision="r1",
        owners={"publication": "foundation"},
        schemas={"result": "result/v1"},
        )


def test_catalog_from_capabilities_and_identity_are_validated():
    value = catalog()
    value.validate()
    assert value.name == "foundation"
    assert value.revision == "r1"


def test_catalog_parser_rejects_missing_required_fields():
    broken = dict(BASE_CAPABILITIES)
    broken.pop("role")
    with pytest.raises(ValueError, match="missing required"):
        catalog_from_capabilities(broken, revision="r1")


def test_catalog_parser_rejects_invalid_identity_and_mapping_values():
    with pytest.raises(ValueError):
        ContractCatalog("", "r1", "role", "family", "1", False, "evidence", False, False, {}, {}, {}).validate()
    with pytest.raises(ValueError):
        catalog_from_capabilities(BASE_CAPABILITIES, revision="")
    with pytest.raises(ValueError):
        ContractCatalog("x", "r1", "role", "family", "1", False, "evidence", False, False, {"": "v"}, {}, {}).validate()


def test_catalog_compare_is_compatible_when_identical():
    value = catalog()
    report = compare_catalogs(value, value)
    assert report.compatible is True
    assert report.findings == ()
    assert canonical_json(report) == canonical_json(report)


def test_catalog_compare_detects_authority_capability_owner_and_schema_drift():
    candidate = catalog(
        role="protected-authority",
        promotion_authority=True,
        evidence_authority="different",
        trust_authority=True,
        private_secrets=True,
    )
    candidate = ContractCatalog(
        candidate.name,
        "r2",
        candidate.role,
        candidate.family,
        candidate.family_contract_version,
        candidate.promotion_authority,
        candidate.evidence_authority,
        candidate.trust_authority,
        candidate.private_secrets,
        {"publication": "v2", "extra": "v1"},
        {"publication": "operations"},
        {"result": "result/v2"},
    )
    report = compare_catalogs(catalog(), candidate, required_capabilities=("publication", "missing"))
    assert report.compatible is False
    fields = {finding.field for finding in report.findings}
    assert "role" in fields
    assert "capability.publication" in fields
    assert "capability.missing" in fields
    assert "owner.publication" in fields
    assert "schema.result" in fields
    assert canonical_json(report) == canonical_json(report)


def test_drift_report_and_finding_validation():
    finding = compare_catalogs(catalog(), catalog()).findings
    report = DriftReport(DRIFT_CONTRACT_VERSION, True, finding)
    report.validate()
    with pytest.raises(ValueError):
        DriftReport("bad", True, ()).validate()
    with pytest.raises(ValueError):
        DriftReport(DRIFT_CONTRACT_VERSION, True, (type("F", (), {"repository": "", "field": "x"})(),)).validate()
