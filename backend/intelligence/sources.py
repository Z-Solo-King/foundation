from dataclasses import dataclass
from enum import StrEnum
import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


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


def source_origin_fingerprint(url: str, *, publisher_hint: str | None = None) -> str:
    """Fingerprint the likely information origin, not merely the source ID."""
    canonical = canonical_source_url(url)
    parsed = urlparse(canonical)
    origin = publisher_hint.strip().lower() if publisher_hint and publisher_hint.strip() else parsed.hostname.lower()
    material = f"{origin}|{parsed.path.split('/')[1] if parsed.path.strip('/') else ''}"
    return hashlib.sha256(material.encode()).hexdigest()


@dataclass(frozen=True)
class SourceLineage:
    source_id: str
    source_family: str
    parent_source_id: str | None = None
    lineage_type: str = "origin"
    origin_fingerprint: str = ""
    republisher_of: str | None = None

    def validate(self) -> None:
        if not self.source_id.strip() or not self.source_family.strip():
            raise ValueError("source_id and source_family must not be empty")
        if self.lineage_type not in {"origin", "republished", "derived"}:
            raise ValueError("invalid lineage_type")
        if not self.origin_fingerprint.strip():
            raise ValueError("origin_fingerprint must not be empty")
        if self.lineage_type == "republished" and not self.republisher_of and not self.parent_source_id:
            raise ValueError("republished lineage must identify its origin")


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
        canonical = canonical_source_url(self.url)
        if self.lineage_type not in {"origin", "republished", "derived"}:
            raise ValueError("invalid lineage_type")
        if self.lineage_type == "republished" and not self.parent_source_id:
            raise ValueError("republished source requires parent_source_id")
        fingerprint = self.origin_fingerprint or source_origin_fingerprint(canonical)
        if not fingerprint:
            raise ValueError("source origin fingerprint required")

    def lineage(self) -> SourceLineage:
        fingerprint = self.origin_fingerprint or source_origin_fingerprint(self.url)
        return SourceLineage(
            source_id=self.source_id,
            source_family=self.family_id or fingerprint,
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


def sources_are_independent(left: SourceLineage, right: SourceLineage) -> bool:
    """Compute independence from origin overlap rather than source-family IDs."""
    left.validate()
    right.validate()
    if left.source_id == right.source_id:
        return False
    if left.origin_fingerprint == right.origin_fingerprint:
        return False
    if left.source_id in {right.parent_source_id, right.republisher_of}:
        return False
    if right.source_id in {left.parent_source_id, left.republisher_of}:
        return False
    return True
