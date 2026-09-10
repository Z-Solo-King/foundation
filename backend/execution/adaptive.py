from dataclasses import dataclass


@dataclass(frozen=True)
class AcquisitionStrategy:
    name: str
    priority: int
    requires_browser: bool = False
    enabled: bool = True


DEFAULT_STRATEGIES = (
    AcquisitionStrategy("direct_http", 1),
    AcquisitionStrategy("public_api", 2),
    AcquisitionStrategy("feed", 3),
    AcquisitionStrategy("sitemap", 4),
    AcquisitionStrategy("embedded_data", 5),
    AcquisitionStrategy("browser", 6, True),
)


def choose_strategy(browser_allowed: bool = True) -> AcquisitionStrategy:
    for x in DEFAULT_STRATEGIES:
        if x.enabled and (browser_allowed or not x.requires_browser):
            return x
    raise RuntimeError("no acquisition strategy available")
