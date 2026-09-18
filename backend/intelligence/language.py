from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re


LANGUAGE_CONTRACT_VERSION = "multilingual-evidence/v1"
_LANGUAGE_RE = re.compile(r"^[a-z]{2,3}(?:-[a-z0-9]{2,8})*$")


def normalize_language_tag(value: str) -> str:
    tag = value.strip().replace("_", "-").casefold()
    if not _LANGUAGE_RE.fullmatch(tag):
        raise ValueError("language tag is invalid")
    parts = tag.split("-")
    return parts[0] + "".join("-" + part for part in parts[1:])


@dataclass(frozen=True)
class LanguageSpan:
    span_id: str
    language: str
    detected_confidence_milli: int
    artifact_id: str
    text_fingerprint: str

    def validate(self) -> None:
        if not self.span_id.strip() or not self.artifact_id.strip():
            raise ValueError("span_id and artifact_id are required")
        normalize_language_tag(self.language)
        if not 0 <= self.detected_confidence_milli <= 1_000:
            raise ValueError("detected_confidence_milli must be between 0 and 1000")
        if len(self.text_fingerprint) != 64 or any(ch not in "0123456789abcdef" for ch in self.text_fingerprint.lower()):
            raise ValueError("text_fingerprint must be SHA-256")


@dataclass(frozen=True)
class TranslationArtifact:
    translation_id: str
    source_span_ids: tuple[str, ...]
    source_language: str
    target_language: str
    method: str
    version: str
    derived_fingerprint: str
    preserves_qualifiers: bool
    preserves_negation: bool
    preserves_units: bool

    def validate(self) -> None:
        if not self.translation_id.strip() or not self.source_span_ids:
            raise ValueError("translation identity and source spans are required")
        normalize_language_tag(self.source_language)
        normalize_language_tag(self.target_language)
        if normalize_language_tag(self.source_language) == normalize_language_tag(self.target_language):
            raise ValueError("translation must cross language boundaries")
        if not self.method.strip() or not self.version.strip():
            raise ValueError("translation method and version are required")
        if len(self.derived_fingerprint) != 64 or any(ch not in "0123456789abcdef" for ch in self.derived_fingerprint.lower()):
            raise ValueError("derived_fingerprint must be SHA-256")
        if not (self.preserves_qualifiers and self.preserves_negation and self.preserves_units):
            raise ValueError("translation cannot claim evidence strength unless qualifiers, negation and units are preserved")


@dataclass(frozen=True)
class ClaimLanguageAlignment:
    alignment_id: str
    source_claim_id: str
    target_claim_id: str
    translation_id: str
    source_language: str
    target_language: str
    status: str
    provenance_preserved: bool

    def validate(self) -> None:
        if not all(item.strip() for item in (self.alignment_id, self.source_claim_id, self.target_claim_id, self.translation_id)):
            raise ValueError("alignment identity fields are required")
        normalize_language_tag(self.source_language)
        normalize_language_tag(self.target_language)
        if self.status not in {"aligned", "qualified", "unknown", "conflict"}:
            raise ValueError("alignment status is invalid")
        if self.status in {"aligned", "qualified"} and not self.provenance_preserved:
            raise ValueError("positive alignment requires preserved provenance")


def text_fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
