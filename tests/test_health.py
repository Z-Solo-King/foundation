from backend.health.check import check_health

def test_health():
    health = check_health()
    assert health.status == "ok"


def test_health_payload_includes_immutable_release_identity():
    from types import SimpleNamespace
    from backend.worker_diagnostics import health_payload

    payload = health_payload(SimpleNamespace(
        ENVIRONMENT="production",
        RELEASE_FOUNDATION_SHA="foundation-test-sha",
        RELEASE_OPERATIONS_REF="operations-test-sha",
    ))
    assert payload["release"] == {
        "foundation_sha": "foundation-test-sha",
        "operations_ref": "operations-test-sha",
    }
