"""HTTP API compatibility exports."""

from .main import health_endpoint


def health_response():
    """Backward-compatible health response used by public tests/clients."""
    return health_endpoint()


__all__ = ["health_response", "health_endpoint"]
