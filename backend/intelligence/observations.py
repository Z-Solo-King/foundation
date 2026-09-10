from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Observation:
    observation_id: str
    source_url: str
    content: str
    observed_at: datetime
    source_id: str | None = None

    @classmethod
    def create(cls, observation_id, *args, source_id=None, source_url=None, content=None):
        if args:
            if len(args) == 2:
                if source_url is not None or content is not None or source_id is not None:
                    raise TypeError("ambiguous observation arguments")
                source_url, content = args
            elif len(args) == 3:
                if source_url is not None or content is not None or source_id is not None:
                    raise TypeError("ambiguous observation arguments")
                source_id, source_url, content = args
            else:
                raise TypeError("Observation.create expects 3 or 4 positional arguments")
        if source_url is None or content is None:
            raise TypeError("source_url and content are required")
        return cls(
            observation_id=observation_id,
            source_url=source_url,
            content=content,
            observed_at=datetime.now(timezone.utc),
            source_id=source_id,
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
