import copy

from backend.evidence_publication import package_digest, package_signature, verify_package


def base_package():
    package = {
        "schema": "evidence-package/v1",
        "run_id": "run-1",
        "lineage": {"observation_ids": ["obs-1"]},
        "claims": [{"claim": "claim", "evidence_ids": ["obs-1"]}],
    }
    package["content_digest"] = package_digest(package)
    package["signature"] = package_signature(package, "secret")
    return package


def check(package, **kwargs):
    return verify_package(package, secret="secret", run_id="run-1", observed_ids={"obs-1"}, **kwargs)


def test_rejects_missing_secret_and_non_object():
    package = base_package()
    assert verify_package(package, secret="", run_id="run-1", observed_ids={"obs-1"})[0] is False
    assert verify_package([], secret="secret", run_id="run-1", observed_ids={"obs-1"})[0] is False


def test_rejects_wrong_schema_and_run_binding():
    package = base_package()
    wrong = copy.deepcopy(package)
    wrong["schema"] = "other/v1"
    assert check(wrong)[0] is False
    wrong = copy.deepcopy(package)
    wrong["run_id"] = "run-2"
    wrong["content_digest"] = package_digest(wrong)
    wrong["signature"] = package_signature(wrong, "secret")
    assert check(wrong)[0] is False


def test_rejects_missing_lineage_variants():
    for lineage in [None, {}, {"observation_ids": []}, {"observation_ids": [1]}, {"observation_ids": ["foreign"]}]:
        package = base_package()
        package["lineage"] = lineage
        package["content_digest"] = package_digest(package)
        package["signature"] = package_signature(package, "secret")
        assert check(package)[0] is False


def test_rejects_invalid_claim_variants():
    for claims in [None, [], [{}], [{"claim": ""}], [{"claim": "ok", "evidence_ids": []}], [{"claim": "ok", "evidence_ids": ["foreign"]}]]:
        package = base_package()
        package["claims"] = claims
        package["content_digest"] = package_digest(package)
        package["signature"] = package_signature(package, "secret")
        assert check(package)[0] is False
