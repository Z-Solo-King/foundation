"""Research synthesis layer.

Produces user-facing answers from verified evidence and explicit uncertainty.
Cites the evidence chain and never allows corroboration to hide contradiction.
"""

from dataclasses import dataclass
from typing import Any

from backend.execution.engine import ResearchRun
from backend.intelligence.verifier import ClaimStatus


@dataclass(frozen=True)
class SynthesisResult:
    """User-facing research result with evidence citations."""
    question: str
    answer: str
    confidence: str
    supported_by: tuple[str, ...] = ()
    qualified_by: tuple[str, ...] = ()
    contradicted_by: tuple[str, ...] = ()
    unknown_aspects: tuple[str, ...] = ()
    evidence_chain: tuple[dict[str, Any], ...] = ()


def _bucket_claims(verified_claims):
    buckets = {"corroborated": [], "supported": [], "partial": [], "contradicted": [], "unknown": []}
    for claim, result in verified_claims:
        status = getattr(result, "status", ClaimStatus.UNKNOWN)
        key = status if status in buckets else "unknown"
        buckets[key].append((claim, result))
    return buckets


def _confidence(buckets):
    if buckets["contradicted"]:
        return "low" if any(buckets[key] for key in ("corroborated", "supported", "partial")) else "unknown"
    if buckets["corroborated"]:
        return "high"
    if buckets["supported"] and not buckets["partial"]:
        return "medium"
    if buckets["partial"]:
        return "low"
    return "unknown"


def _answer(buckets):
    answer_parts = [claim.text for claim, _ in (
        buckets["corroborated"] + buckets["supported"] + buckets["partial"]
    )]
    if buckets["contradicted"]:
        answer_parts.append(
            "Contradictory evidence exists for: " + "; ".join(claim.text for claim, _ in buckets["contradicted"])
        )
    if buckets["unknown"]:
        answer_parts.append(
            "Unresolved aspects: " + "; ".join(claim.text for claim, _ in buckets["unknown"])
        )
    return "\n".join(answer_parts) if answer_parts else "Evidence is insufficient to answer this question."


def _evidence_chain(run):
    observations = {o.observation_id: o for o in run.observations}
    evidence_chain = []
    for claim, result in run.verified_claims:
        status = getattr(result, "status", ClaimStatus.UNKNOWN)
        for cert in result.supporting_evidence:
            obs = observations.get(cert.observation_id)
            if obs:
                evidence_chain.append({
                    "claim_id": claim.claim_id,
                    "claim": claim.text,
                    "source_url": obs.source_url,
                    "evidence_text": cert.span_text,
                    "retrieved_at": obs.observed_at.isoformat(),
                    "verification_status": status,
                })
    return tuple(evidence_chain)


class ResearchSynthesizer:
    """Synthesizes verified claims and preserves uncertainty."""

    def synthesize(self, run: ResearchRun) -> SynthesisResult:
        """Synthesize verified claims; malformed fields fail closed."""
        contract = getattr(run, "contract", None)
        question = getattr(contract, "question", "")
        if not run.verified_claims:
            return SynthesisResult(question=question, answer="No evidence found to answer this question.", confidence="unknown")
        buckets = _bucket_claims(run.verified_claims)
        return SynthesisResult(
            question=question,
            answer=_answer(buckets),
            confidence=_confidence(buckets),
            supported_by=tuple(claim.claim_id for claim, _ in buckets["corroborated"]),
            qualified_by=tuple(claim.claim_id for claim, _ in buckets["supported"] + buckets["partial"]),
            contradicted_by=tuple(claim.claim_id for claim, _ in buckets["contradicted"]),
            unknown_aspects=tuple(claim.claim_id for claim, _ in buckets["unknown"]),
            evidence_chain=_evidence_chain(run),
        )
