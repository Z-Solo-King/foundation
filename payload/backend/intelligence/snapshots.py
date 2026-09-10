from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class ClaimSnapshot:
    snapshot_id: str
    claim_id: str
    text: str
    observed_at: datetime

    @classmethod
    def create(cls, snapshot_id, claim_id, text):
        return cls(snapshot_id, claim_id, text, datetime.now(timezone.utc))


def changed(previous: ClaimSnapshot, current: ClaimSnapshot) -> bool:
    return previous.claim_id == current.claim_id and previous.text != current.text
