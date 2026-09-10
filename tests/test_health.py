from backend.health.check import check_health

def test_health():
    health = check_health()
    assert health.status == "ok"
