from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Observation:
    observation_id: str
    source_id: str
    source_url: str
    content: str
    observed_at: datetime

    @classmethod
    def create(cls, observation_id, source_id, source_url, content):
        return cls(
            observation_id,
            source_id,
            source_url,
            content,
            datetime.now(timezone.utc),
        )


@dataclass(frozen=True)
class EvidenceSpan:
    observation_id: str
    start: int
    end: int

    def validate(self, observation: Observation):
        if self.observation_id != observation.observation_id:
            raise ValueError("observation ID mismatch")
        if self.start < 0 or self.end < self.start:
            raise ValueError("invalid evidence span")
        if self.end > len(observation.content):
            raise ValueError("evidence span exceeds observation")

    def text_from(self, observation: Observation) -> str:
        self.validate(observation)
        return observation.content[self.start:self.end]
