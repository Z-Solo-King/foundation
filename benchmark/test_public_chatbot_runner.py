from benchmark.public_chatbot_runner import classify_target_health


def test_target_health_classifies_blocked_targets():
    health, action = classify_target_health(100, 100, {"blocked": 100}, {"403": 100})
    assert health == "blocked"
    assert action == "quarantine_until_manual_recheck"


def test_target_health_classifies_rate_limited_targets():
    health, action = classify_target_health(100, 100, {"resource_limited": 100}, {"429": 100})
    assert health == "rate_limited"
    assert action == "exponential_backoff_and_quarantine"


def test_target_health_classifies_transport_failures():
    health, action = classify_target_health(48, 48, {"error": 48}, {})
    assert health == "transport_error"
    assert action == "investigate_dns_tls_or_network_path"


def test_target_health_classifies_intermittent_targets():
    health, action = classify_target_health(48, 24, {"ok": 24, "error": 24}, {"200": 24})
    assert health == "degraded"
    assert action == "retain_for_targeted_recheck"


def test_target_health_classifies_healthy_targets():
    health, action = classify_target_health(48, 0, {"ok": 48}, {"200": 48})
    assert health == "healthy"
    assert action == "retain_normal_sampling"
