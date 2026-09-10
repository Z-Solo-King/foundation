from dataclasses import dataclass

from backend.sources.model import Source


@dataclass(frozen=True)
class SourcePolicy:
    allowed: bool = True
    retain_content: bool = False
    max_requests: int = 5


def evaluate_source(source: Source, policy: SourcePolicy) -> bool:
    return policy.allowed and bool(source.url)
