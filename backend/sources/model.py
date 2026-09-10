from dataclasses import dataclass
from enum import StrEnum


class SourceType(StrEnum):
    WEB = "web"
    API = "api"
    DOCUMENT = "document"
    REPOSITORY = "repository"
    VIDEO = "video"
    COMMUNITY = "community"


@dataclass(frozen=True)
class Source:
    url: str
    source_type: SourceType
    title: str = ""
