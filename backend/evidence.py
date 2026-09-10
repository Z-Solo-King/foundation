from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Observation:
    observation_id: str
    source_url: str
    content: str
    observed_at: datetime

    @classmethod
    def create(
        cls,
        observation_id: str,
        source_url: str,
        content: str,
    ) -> "Observation":
        return cls(
            observation_id=observation_id,
            source_url=source_url,
            content=content,
            observed_at=datetime.now(timezone.utc),
        )


@dataclass(frozen=True)
class EvidenceSpan:
    observation_id: str
    start: int
    end: int

    def text_from(self, observation: Observation) -> str:
        if observation.observation_id != self.observation_id:
            raise ValueError("Observation ID mismatch")

        if self.start < 0 or self.end < self.start:
            raise ValueError("Invalid evidence span")

        return observation.content[self.start:self.end]
