from dataclasses import dataclass


@dataclass
class ResourceBudget:
    requests: int = 100
    evidence_items: int = 100
    ai_calls: int = 10

    def consume(self, field: str, amount: int = 1):
        if amount < 0:
            raise ValueError("amount must not be negative")
        current = getattr(self, field)
        if current < amount:
            raise RuntimeError(f"resource budget exhausted: {field}")
        setattr(self, field, current - amount)

    def consume_requests(self, amount: int = 1):
        self.consume("requests", amount)

    def consume_evidence(self, amount: int = 1):
        self.consume("evidence_items", amount)

    def consume_ai_calls(self, amount: int = 1):
        self.consume("ai_calls", amount)

    def remaining(self):
        return {
            "requests": self.requests,
            "evidence_items": self.evidence_items,
            "ai_calls": self.ai_calls,
        }
