from dataclasses import dataclass


class ResourceError(RuntimeError):
    """Raised when a hard execution budget is exhausted."""


@dataclass
class ResourceBudget:
    requests: int = 100
    evidence_items: int = 100
    ai_calls: int = 10
    # Compatibility alias used by router and legacy plan contracts.
    inference_calls: int | None = None

    def __post_init__(self):
        if self.inference_calls is not None:
            if self.inference_calls < 0:
                raise ValueError("inference_calls must not be negative")
            self.ai_calls = self.inference_calls

    @property
    def inference_remaining(self) -> int:
        return self.ai_calls

    def consume(self, field: str, amount: int = 1):
        if amount < 0:
            raise ValueError("amount must not be negative")
        if not hasattr(self, field):
            raise ValueError(f"unknown resource field: {field}")
        current = getattr(self, field)
        if current is None:
            raise ValueError(f"resource field {field} is not configured")
        if current < amount:
            raise ResourceError(f"resource budget exhausted: {field}")
        setattr(self, field, current - amount)

    def consume_requests(self, amount: int = 1):
        self.consume("requests", amount)

    def consume_evidence(self, amount: int = 1):
        self.consume("evidence_items", amount)

    def consume_ai_calls(self, amount: int = 1):
        self.consume("ai_calls", amount)

    def consume_inference(self, amount: int = 1):
        self.consume("ai_calls", amount)

    def remaining(self):
        return {
            "requests": self.requests,
            "evidence_items": self.evidence_items,
            "ai_calls": self.ai_calls,
            "inference_calls": self.ai_calls,
        }
