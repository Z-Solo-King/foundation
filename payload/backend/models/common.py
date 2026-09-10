from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Timestamped:
    created_at: datetime

    @classmethod
    def now(cls):
        return cls(created_at=datetime.now(timezone.utc))
