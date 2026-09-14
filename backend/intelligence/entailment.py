"""Public-safe deterministic claim-to-evidence entailment primitive.

Private policy may adjudicate ambiguous results, but this module never owns
that policy or any model/provider decision.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from backend.intelligence.observations import EvidenceSpan, Observation

_TOKEN_RE = re.compile(r"[\w%$€£.-]+", re.UNICODE)
_NEGATION = {"not", "no", "never", "none", "without", "cannot", "can't", "isn't", "aren't", "doesn't", "don't"}


class EntailmentStatus:
    SUPPORTED = "supported"
    AMBIGUOUS = "ambiguous"
    UNSUPPORTED = "unsupported"
    INVALID = "invalid"


@dataclass(frozen=True)
class EntailmentResult:
    status: str
    score: float
    reason: str

    @property
    def accepted(self) -> bool:
        return self.status == EntailmentStatus.SUPPORTED


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text)]


def _negations(tokens: list[str]) -> set[str]:
    return {token for token in tokens if token in _NEGATION}


def verify_claim_entailment(
    claim_text: str,
    observation: Observation,
    span: EvidenceSpan,
    *,
    ambiguous_threshold: float = 0.60,
    supported_threshold: float = 0.85,
) -> EntailmentResult:
    """Return deterministic support status; ambiguous cases remain ambiguous."""
    try:
        evidence_text = span.text_from(observation)
    except ValueError as exc:
        return EntailmentResult(EntailmentStatus.INVALID, 0.0, str(exc))

    claim_tokens = _tokens(claim_text)
    evidence_tokens = _tokens(evidence_text)
    if not claim_tokens or not evidence_tokens:
        return EntailmentResult(EntailmentStatus.UNSUPPORTED, 0.0, "claim or evidence is empty")

    normalized_claim = " ".join(claim_tokens)
    normalized_evidence = " ".join(evidence_tokens)
    if normalized_claim in normalized_evidence:
        return EntailmentResult(EntailmentStatus.SUPPORTED, 1.0, "normalized claim occurs in cited evidence")

    claim_set = set(claim_tokens)
    evidence_set = set(evidence_tokens)
    coverage = len(claim_set & evidence_set) / len(claim_set)
    if bool(_negations(claim_tokens)) != bool(_negations(evidence_tokens)):
        return EntailmentResult(EntailmentStatus.UNSUPPORTED, coverage, "negation polarity mismatch")
    if coverage >= supported_threshold:
        return EntailmentResult(EntailmentStatus.SUPPORTED, coverage, "high deterministic lexical support")
    if coverage >= ambiguous_threshold:
        return EntailmentResult(EntailmentStatus.AMBIGUOUS, coverage, "ambiguous semantic support requires policy-authorized adjudication")
    return EntailmentResult(EntailmentStatus.UNSUPPORTED, coverage, "insufficient deterministic support")
