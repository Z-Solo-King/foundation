from dataclasses import dataclass
from enum import StrEnum
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from backend.intelligence.lineage import SourceLineage, is_independent as sources_are_independent


class SourceType(StrEnum):
    WEB = "web"
    API = "api"
    DOCUMENT = "document"
    REPOSITORY = "repository"
    VIDEO = "video"
    COMMUNITY = "community"


_TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid"}


def canonical_source_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("source URL must be an absolute HTTP(S) URL")
    host = parsed.hostname.lower() if parsed.hostname else ""
    port = parsed.port
    netloc = host
    if port and not ((parsed.scheme == "http" and port == 80) or (parsed.scheme == "https" and port == 443)):
        netloc = f"{host}:{port}"
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    pairs = sorted((key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True) if key not in _TRACKING_PARAMS)
    query = urlencode(pairs)
    return urlunparse((parsed.scheme, netloc, path, "", query, ""))


@dataclass(frozen=True)
class Source:
    source_id: str
    url: str
    source_type: SourceType
    title: str = ""
    family_id: str | None = None
    parent_source_id: str | None = None
    lineage_type: str = "origin"
    origin_fingerprint: str | None = None

    def validate(self):
        canonical_source_url(self.url)
        if self.lineage_type not in {"origin", "republished", "derived"}:
            raise ValueError("invalid lineage_type")
        if self.lineage_type == "republished" and not self.parent_source_id:
            raise ValueError("republished source requires parent_source_id")

    def lineage(self, fingerprint: str) -> SourceLineage:
        return SourceLineage(
            source_id=self.source_id,
            family_id=self.family_id or fingerprint,
            parent_source_id=self.parent_source_id,
            lineage_type=self.lineage_type,
            origin_fingerprint=fingerprint,
            republisher_of=self.parent_source_id if self.lineage_type == "republished" else None,
        )


@dataclass(frozen=True)
class SourcePolicy:
    allowed: bool = True
    retain_content: bool = False
    max_requests: int = 5


def evaluate_source(source: Source, policy: SourcePolicy) -> bool:
    source.validate()
    return policy.allowed and policy.max_requests > 0


__all__ = [
    "SourceType",
    "Source",
    "SourcePolicy",
    "SourceLineage",
    "canonical_source_url",
    "evaluate_source",
    "sources_are_independent",
]
