from backend.health.check import check_health


def health_response():
    health = check_health()
    return {
        "status": health.status,
        "app": health.app,
        "version": health.version,
        "environment": health.environment,
    }
