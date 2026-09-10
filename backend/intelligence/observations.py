from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Observation:
    """Canonical observation record.

    Field order preserves the historical positional constructor contract:
    ``(observation_id, source_id, source_url, content, observed_at)``.
    New callers should prefer keywords or ``create``.
    """

    observation_id: str
    source_id: str | None
    source_url: str
    content: str
    observed_at: datetime

    @classmethod
    def create(cls, observation_id, *args, source_id=None, source_url=None, content=None, observed_at=None):
        if args:
            if len(args) == 2:
                if source_url is not None or content is not None or source_id is not None:
                    raise TypeError("ambiguous observation arguments")
                source_url, content = args
            elif len(args) == 3:
                if source_url is not None or content is not None or source_id is not None:
                    raise TypeError("ambiguous observation arguments")
                source_id, source_url, content = args
            elif len(args) == 4:
                if any(value is not None for value in (source_url, content, source_id, observed_at)):
                    raise TypeError("ambiguous observation arguments")
                source_id, source_url, content, observed_at = args
            else:
                raise TypeError("Observation.create expects 3, 4, or 5 positional arguments")
        if source_url is None or content is None:
            raise TypeError("source_url and content are required")
        return cls(
            observation_id=observation_id,
            source_id=source_id,
            source_url=source_url,
            content=content,
            observed_at=observed_at or datetime.now(timezone.utc),
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
