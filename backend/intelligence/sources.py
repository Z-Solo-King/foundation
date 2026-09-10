from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlparse


class SourceType(StrEnum):
    WEB = "web"
    API = "api"
    DOCUMENT = "document"
    REPOSITORY = "repository"
    VIDEO = "video"
    COMMUNITY = "community"


@dataclass(frozen=True)
class Source:
    source_id: str
    url: str
    source_type: SourceType
    title: str = ""
    family_id: str | None = None

    def validate(self) -> None:
        parsed = urlparse(self.url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("source URL must be an absolute HTTP(S) URL")


@dataclass(frozen=True)
class SourcePolicy:
    allowed: bool = True
    retain_content: bool = False
    max_requests: int = 5


def evaluate_source(source: Source, policy: SourcePolicy) -> bool:
    source.validate()
    return policy.allowed and policy.max_requests > 0
