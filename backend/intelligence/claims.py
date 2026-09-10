from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(cls, claim_id: str, text: str):
        if not text.strip():
            raise ValueError("claim text must not be empty")
        return cls(claim_id, text)


@dataclass(frozen=True)
class ClaimVersion:
    claim_id: str
    version: int
    text: str
    valid_from: datetime
    valid_to: datetime | None = None
