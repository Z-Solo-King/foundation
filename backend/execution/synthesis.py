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


class ResearchSynthesizer:
    """Synthesizes verified claims and preserves uncertainty."""

    def synthesize(self, run: ResearchRun) -> SynthesisResult:
        """Synthesize verified claims; malformed fields fail closed."""
        contract = getattr(run, "contract", None)
        question = getattr(contract, "question", "")
        if not run.verified_claims:
            return SynthesisResult(question=question, answer="No evidence found to answer this question.", confidence="unknown")
        groups = self._group_claims(run)
        confidence = self._confidence(groups)
        answer = self._build_answer(groups)
        evidence_chain = self._evidence_chain(run)
        return SynthesisResult(
            question=question,
            answer=answer,
            confidence=confidence,
            supported_by=tuple(claim.claim_id for claim, _ in groups[ClaimStatus.CORROBORATED]),
            qualified_by=tuple(claim.claim_id for claim, _ in groups[ClaimStatus.SUPPORTED] + groups[ClaimStatus.PARTIAL]),
            contradicted_by=tuple(claim.claim_id for claim, _ in groups[ClaimStatus.CONTRADICTED]),
            unknown_aspects=tuple(claim.claim_id for claim, _ in groups[ClaimStatus.UNKNOWN]),
            evidence_chain=tuple(evidence_chain),
        )

    @staticmethod
    def _group_claims(run):
        groups = {status: [] for status in (
            ClaimStatus.CORROBORATED, ClaimStatus.SUPPORTED, ClaimStatus.PARTIAL,
            ClaimStatus.CONTRADICTED, ClaimStatus.UNKNOWN,
        )}
        for claim, result in run.verified_claims:
            status = getattr(result, "status", ClaimStatus.UNKNOWN)
            groups.setdefault(status, []).append((claim, result))
        return groups

    @staticmethod
    def _confidence(groups):
        corroborated = groups[ClaimStatus.CORROBORATED]
        supported = groups[ClaimStatus.SUPPORTED]
        partial = groups[ClaimStatus.PARTIAL]
        contradicted = groups[ClaimStatus.CONTRADICTED]
        if contradicted:
            return "low" if (corroborated or supported or partial) else "unknown"
        if corroborated:
            return "high"
        if supported and not partial:
            return "medium"
        if partial:
            return "low"
        return "unknown"

    @staticmethod
    def _build_answer(groups):
        answer_parts = [claim.text for claim, _ in groups[ClaimStatus.CORROBORATED] + groups[ClaimStatus.SUPPORTED] + groups[ClaimStatus.PARTIAL]]
        contradicted = groups[ClaimStatus.CONTRADICTED]
        unknown = groups[ClaimStatus.UNKNOWN]
        if contradicted:
            answer_parts.append("Contradictory evidence exists for: " + "; ".join(claim.text for claim, _ in contradicted))
        if unknown:
            answer_parts.append("Unresolved aspects: " + "; ".join(claim.text for claim, _ in unknown))
        return "\n".join(answer_parts) if answer_parts else "Evidence is insufficient to answer this question."

    @staticmethod
    def _evidence_chain(run):
        observations = {o.observation_id: o for o in run.observations}
        evidence_chain = []
        for claim, result in run.verified_claims:
            for cert in result.supporting_evidence:
                obs = observations.get(cert.observation_id)
                if obs:
                    evidence_chain.append({
                        "claim_id": claim.claim_id,
                        "claim": claim.text,
                        "source_url": obs.source_url,
                        "evidence_text": cert.span_text,
                        "retrieved_at": obs.observed_at.isoformat(),
                        "verification_status": getattr(result, "status", ClaimStatus.UNKNOWN),
                    })
        return evidence_chain
