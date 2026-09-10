from dataclasses import dataclass

from backend.sources.model import Source


@dataclass(frozen=True)
class SourcePolicy:
    allowed: bool = True
    retain_content: bool = False
    max_requests: int = 5

    def validate(self) -> None:
        if self.max_requests < 0:
            raise ValueError("max_requests must be non-negative")


def evaluate_source(source: Source, policy: SourcePolicy) -> bool:
    policy.validate()
    return policy.allowed and bool(source.url.strip())
