from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str
    created_at: datetime

    @classmethod
    def create(cls, claim_id: str, text: str):
        if not text.strip():
            raise ValueError("claim text must not be empty")
        return cls(
            claim_id=claim_id,
            text=text,
            created_at=datetime.now(timezone.utc),
        )


@dataclass(frozen=True)
class ClaimVersion:
    claim_id: str
    version: int
    text: str
    valid_from: datetime
    valid_to: datetime | None = None
