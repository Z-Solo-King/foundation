from backend.api import health_response


def test_health_response():
    response = health_response()
    assert response["status"] == "ok"
    assert response["app"] == "Research Intelligence Engine"
