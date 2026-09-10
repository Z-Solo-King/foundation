from dataclasses import dataclass


@dataclass
class ResourceBudget:
    requests: int = 100
    evidence_items: int = 100
    ai_calls: int = 10

    def consume_requests(self, amount: int = 1) -> None:
        self._consume("requests", amount)

    def consume_evidence(self, amount: int = 1) -> None:
        self._consume("evidence_items", amount)

    def consume_ai_calls(self, amount: int = 1) -> None:
        self._consume("ai_calls", amount)

    def remaining(self) -> dict[str, int]:
        return {
            "requests": self.requests,
            "evidence_items": self.evidence_items,
            "ai_calls": self.ai_calls,
        }

    def _consume(self, name: str, amount: int) -> None:
        if amount < 0:
            raise ValueError("amount must not be negative")
        current = getattr(self, name)
        if current < amount:
            raise RuntimeError(f"resource budget exhausted: {name}")
        setattr(self, name, current - amount)
