from dataclasses import dataclass

from backend.core.config import settings


@dataclass(frozen=True)
class HealthStatus:
    status: str
    app: str
    version: str
    environment: str


def check_health() -> HealthStatus:
    return HealthStatus(
        status="ok",
        app=settings.app_name,
        version=settings.version,
        environment=settings.environment,
    )
