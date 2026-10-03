import json

import pytest

from tools.check_cross_repo_drift import compare_active_family_catalogs


def foundation():
    return {
        "family": "z-solo-king-github-family",
        "family_contract": "docs/FAMILY_MEMBER.md",
        "family_contract_version": "1",
        "name": "foundation",
        "role": "public-contracts",
        "promotion_authority": False,
        "trust_authority": False,
        "private_secrets": False,
        "resource_governance": "operations",
    }


def operations():
    return {
        "family": "z-solo-king-github-family",
        "family_contract": "docs/FAMILY_MEMBER.md",
        "family_contract_version": "1",
        "name": "operations",
        "role": "protected-authority",
        "promotion_authority": True,
        "trust_authority": True,
        "private_secrets": True,
    }


def test_active_family_catalogs_are_compatible():
    report = compare_active_family_catalogs(foundation(), operations())
    assert report.compatible is True
    assert report.findings == ()


@pytest.mark.parametrize(
    "name,change",
    [
        ("family", lambda value: value | {"family": "wrong-family"}),
        ("foundation-role", lambda value: {**value, "role": "protected-authority"}),
        ("operations-authority", lambda value: {**value, "promotion_authority": False}),
        ("family-contract-version", lambda value: {**value, "family_contract_version": "2"}),
        ("resource-owner", lambda value: {**value, "resource_governance": "foundation"}),
    ],
)
def test_boundary_drift_fails_closed(name, change):
    left = foundation()
    right = operations()
    if name == "family":
        left = change(left)
    elif name == "foundation-role" or name == "family-contract-version" or name == "resource-owner":
        left = change(left)
    else:
        right = change(right)
    report = compare_active_family_catalogs(left, right)
    assert report.compatible is False
    assert report.findings


def test_report_is_json_serializable():
    report = compare_active_family_catalogs(foundation(), operations())
    json.dumps(
        {
            "schema_version": report.schema_version,
            "compatible": report.compatible,
            "findings": [finding.message for finding in report.findings],
        }
    )


def test_contract_drift_version_is_stable():
    report = compare_active_family_catalogs(foundation(), operations())
    assert report.schema_version == "cross-repo-drift/v1"
