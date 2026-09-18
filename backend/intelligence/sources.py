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


class DisclosureState(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    UNKNOWN = "unknown"


class AccessState(StrEnum):
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    RESTRICTED = "restricted"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SourcePolicy:
    allowed: bool = True
    retain_content: bool = False
    max_requests: int = 5
    revision: str = "source-policy/v1"
    access: AccessState = AccessState.PUBLIC
    retention_seconds: int | None = 86_400
    disclosure: DisclosureState = DisclosureState.PUBLIC
    revalidate_after_seconds: int | None = None

    def validate(self) -> None:
        if not self.revision.strip():
            raise ValueError("source policy revision is required")
        if self.max_requests < 1:
            raise ValueError("max_requests must be positive")
        if self.retention_seconds is not None and self.retention_seconds < 0:
            raise ValueError("retention_seconds must be non-negative or None")
        if self.revalidate_after_seconds is not None and self.revalidate_after_seconds < 0:
            raise ValueError("revalidate_after_seconds must be non-negative or None")
        if not isinstance(self.access, AccessState) or not isinstance(self.disclosure, DisclosureState):
            raise ValueError("source access/disclosure state is invalid")


@dataclass(frozen=True)
class SourcePolicyDecision:
    allowed: bool
    reason: str
    policy_revision: str


def evaluate_source_policy(source: Source, policy: SourcePolicy) -> SourcePolicyDecision:
    source.validate()
    policy.validate()
    if not policy.allowed:
        return SourcePolicyDecision(False, "source access is disabled by policy", policy.revision)
    if policy.max_requests < 1:
        return SourcePolicyDecision(False, "source request budget is exhausted", policy.revision)
    if policy.access is AccessState.UNKNOWN:
        return SourcePolicyDecision(False, "source access classification is unknown", policy.revision)
    if policy.disclosure is DisclosureState.UNKNOWN:
        return SourcePolicyDecision(False, "source disclosure classification is unknown", policy.revision)
    if policy.access is AccessState.RESTRICTED and policy.disclosure is DisclosureState.PUBLIC:
        return SourcePolicyDecision(False, "restricted source cannot be public-disclosure eligible", policy.revision)
    if policy.access is AccessState.AUTHENTICATED and not policy.retain_content:
        return SourcePolicyDecision(True, "authenticated source allowed with metadata-only retention", policy.revision)
    return SourcePolicyDecision(True, "source is eligible under current access policy", policy.revision)


def evaluate_source(source: Source, policy: SourcePolicy) -> bool:
    return evaluate_source_policy(source, policy).allowed


__all__ = [
    "SourceType",
    "Source",
    "SourcePolicy",
    "SourceLineage",
    "canonical_source_url",
    "evaluate_source",
    "sources_are_independent",
]
