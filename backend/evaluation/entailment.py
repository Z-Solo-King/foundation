"""Deterministic-first semantic claim-to-evidence verification."""

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
    """Verify that a cited span supports the claim without caller-supplied flags.

    Exact normalized inclusion is accepted deterministically. Otherwise token
    coverage is used as a conservative lexical signal. Ambiguous cases are
    explicitly separated so an AI adjudicator can be invoked by policy.
    """
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

    claim_neg = _negations(claim_tokens)
    evidence_neg = _negations(evidence_tokens)
    if bool(claim_neg) != bool(evidence_neg):
        return EntailmentResult(EntailmentStatus.UNSUPPORTED, coverage, "negation polarity mismatch")

    if coverage >= supported_threshold:
        return EntailmentResult(EntailmentStatus.SUPPORTED, coverage, "high deterministic lexical support")
    if coverage >= ambiguous_threshold:
        return EntailmentResult(EntailmentStatus.AMBIGUOUS, coverage, "ambiguous semantic support requires adjudication")
    return EntailmentResult(EntailmentStatus.UNSUPPORTED, coverage, "insufficient deterministic support")


def adjudicate_ambiguous(result: EntailmentResult, ai_supported: bool) -> EntailmentResult:
    """Convert an ambiguous result only after explicit policy-authorized AI review."""
    if result.status != EntailmentStatus.AMBIGUOUS:
        return result
    if ai_supported:
        return EntailmentResult(EntailmentStatus.SUPPORTED, result.score, "AI adjudicated ambiguous evidence as supporting")
    return EntailmentResult(EntailmentStatus.UNSUPPORTED, result.score, "AI adjudicated ambiguous evidence as insufficient")
