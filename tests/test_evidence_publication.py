import copy

from backend.evidence_publication import package_digest, package_signature, verify_package


def _package():
    package = {
        "schema": "evidence-package/v1",
        "run_id": "run-1",
        "lineage": {"observation_ids": ["run-1:obs:0"]},
        "claims": [{"claim": "verified claim", "evidence_ids": ["run-1:obs:0"]}],
    }
    package["content_digest"] = package_digest(package)
    package["signature"] = package_signature(package, "test-secret")
    return package


def test_verified_package_requires_digest_signature_and_lineage():
    package = _package()
    assert verify_package(package, secret="test-secret", run_id="run-1", observed_ids={"run-1:obs:0"}) == (True, "verified")


def test_tampered_package_is_rejected():
    package = _package()
    tampered = copy.deepcopy(package)
    tampered["claims"][0]["claim"] = "tampered"
    ok, reason = verify_package(tampered, secret="test-secret", run_id="run-1", observed_ids={"run-1:obs:0"})
    assert not ok
    assert "digest" in reason


def test_wrong_signature_and_foreign_lineage_are_rejected():
    package = _package()
    wrong_key = copy.deepcopy(package)
    wrong_key["signature"] = package_signature(wrong_key, "wrong-secret")
    assert verify_package(wrong_key, secret="test-secret", run_id="run-1", observed_ids={"run-1:obs:0"}) == (False, "evidence package signature verification failed")

    foreign = copy.deepcopy(package)
    foreign["lineage"]["observation_ids"] = ["run-2:obs:0"]
    foreign["content_digest"] = package_digest(foreign)
    foreign["signature"] = package_signature(foreign, "test-secret")
    ok, reason = verify_package(foreign, secret="test-secret", run_id="run-1", observed_ids={"run-1:obs:0"})
    assert not ok
    assert "outside the research run" in reason
