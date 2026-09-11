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
    """Synthesizes research results from verified claims."""

    def synthesize(self, run: ResearchRun) -> SynthesisResult:
        """Synthesize verified claims; malformed statuses fail closed as unknown."""
        if not run.verified_claims:
            return SynthesisResult(
                question=run.contract.question,
                answer="No evidence found to answer this question.",
                confidence="unknown",
            )

        corroborated: list[tuple[Any, Any]] = []
        supported: list[tuple[Any, Any]] = []
        partial: list[tuple[Any, Any]] = []
        contradicted: list[tuple[Any, Any]] = []
        unknown: list[tuple[Any, Any]] = []

        for claim, result in run.verified_claims:
            status = getattr(result, "status", ClaimStatus.UNKNOWN)
            if status == ClaimStatus.CORROBORATED:
                corroborated.append((claim, result))
            elif status == ClaimStatus.SUPPORTED:
                supported.append((claim, result))
            elif status == ClaimStatus.PARTIAL:
                partial.append((claim, result))
            elif status == ClaimStatus.CONTRADICTED:
                contradicted.append((claim, result))
            else:
                unknown.append((claim, result))

        # Contradicted claims always lower confidence. A mixed result is never
        # presented as high-confidence simply because one claim is corroborated.
        if contradicted:
            confidence = "low" if (corroborated or supported or partial) else "unknown"
        elif corroborated:
            confidence = "high"
        elif supported and not partial:
            confidence = "medium"
        elif partial:
            confidence = "low"
        else:
            confidence = "unknown"

        answer_parts: list[str] = []
        for claim, _ in corroborated + supported + partial:
            answer_parts.append(claim.text)
        if contradicted:
            answer_parts.append(
                "Contradictory evidence exists for: " + "; ".join(claim.text for claim, _ in contradicted)
            )
        if unknown:
            answer_parts.append(
                "Unresolved aspects: " + "; ".join(claim.text for claim, _ in unknown)
            )
        answer = "\n".join(answer_parts) if answer_parts else "Evidence is insufficient to answer this question."

        evidence_chain: list[dict[str, Any]] = []
        observations = {o.observation_id: o for o in run.observations}
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

        return SynthesisResult(
            question=run.contract.question,
            answer=answer,
            confidence=confidence,
            supported_by=tuple(claim.claim_id for claim, _ in corroborated),
            qualified_by=tuple(claim.claim_id for claim, _ in supported + partial),
            contradicted_by=tuple(claim.claim_id for claim, _ in contradicted),
            unknown_aspects=tuple(claim.claim_id for claim, _ in unknown),
            evidence_chain=tuple(evidence_chain),
        )
