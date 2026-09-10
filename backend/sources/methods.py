from dataclasses import dataclass


@dataclass(frozen=True)
class AcquisitionMethod:
    name: str
    priority: int
    enabled: bool = True


DEFAULT_METHODS = (
    AcquisitionMethod("direct_http", 1),
    AcquisitionMethod("public_api", 2),
    AcquisitionMethod("feed", 3),
    AcquisitionMethod("sitemap", 4),
    AcquisitionMethod("embedded_data", 5),
)
