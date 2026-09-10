from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True, init=False)
class Observation:
    """Canonical observation record with backward-compatible construction.

    Supported positional forms:
      ``Observation(id, source_id, url, content, observed_at)`` (historical)
      ``Observation(id, url, content, observed_at)`` (lightweight)

    Keyword construction is preferred for new code.
    """

    observation_id: str
    source_url: str
    content: str
    observed_at: datetime
    source_id: str | None = None

    def __init__(
        self,
        observation_id: str,
        *args,
        source_id: str | None = None,
        source_url: str | None = None,
        content: str | None = None,
        observed_at: datetime | None = None,
    ):
        if args:
            if any(value is not None for value in (source_id, source_url, content, observed_at)):
                raise TypeError("ambiguous observation arguments")
            if len(args) == 3:
                source_url, content, observed_at = args
            elif len(args) == 4:
                source_id, source_url, content, observed_at = args
            else:
                raise TypeError("Observation expects 4 or 5 total positional arguments")
        if source_url is None or content is None:
            raise TypeError("source_url and content are required")
        object.__setattr__(self, "observation_id", observation_id)
        object.__setattr__(self, "source_url", source_url)
        object.__setattr__(self, "content", content)
        object.__setattr__(self, "observed_at", observed_at or datetime.now(timezone.utc))
        object.__setattr__(self, "source_id", source_id)

    @classmethod
    def create(cls, observation_id, *args, source_id=None, source_url=None, content=None, observed_at=None):
        if args:
            if any(value is not None for value in (source_url, content, source_id, observed_at)):
                raise TypeError("ambiguous observation arguments")
            if len(args) == 2:
                source_url, content = args
            elif len(args) == 3:
                source_id, source_url, content = args
            elif len(args) == 4:
                source_id, source_url, content, observed_at = args
            else:
                raise TypeError("Observation.create expects 3, 4, or 5 positional arguments")
        return cls(
            observation_id,
            source_id=source_id,
            source_url=source_url,
            content=content,
            observed_at=observed_at,
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
