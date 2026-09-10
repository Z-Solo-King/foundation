"""Research synthesis layer.

Produces user-facing answers from verified evidence and explicit uncertainty.
Cites evidence chain; does not conflate epistemology with ontology.
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
    confidence: str  # high, medium, low, unknown
    supported_by: tuple[str, ...] = ()  # claim IDs with CORROBORATED status
    qualified_by: tuple[str, ...] = ()  # claim IDs with SUPPORTED/PARTIAL status
    contradicted_by: tuple[str, ...] = ()  # claim IDs with CONTRADICTED status
    unknown_aspects: tuple[str, ...] = ()  # aspects without evidence
    evidence_chain: tuple[dict[str, Any], ...] = ()


class ResearchSynthesizer:
    """Synthesizes research results from verified claims."""
    
    def __init__(self):
        pass
    
    def synthesize(self, run: ResearchRun) -> SynthesisResult:
        """Synthesize a final answer from verified claims.
        
        Args:
            run: Completed research run with verified claims
            
        Returns:
            SynthesisResult with answer, confidence, and evidence citations
        """
        if not run.verified_claims:
            return SynthesisResult(
                question=run.contract.question,
                answer="No evidence found to answer this question.",
                confidence="unknown",
            )
        
        # Categorize claims by verification status
        corroborated = []
        supported = []
        partial = []
        contradicted = []
        unknown = []
        
        for claim, result in run.verified_claims:
            entry = {
                "text": claim.text,
                "status": result.status,
                "evidence_count": len(result.supporting_evidence),
                "independent_sources": result.independent_corroboration_count,
            }
            
            if result.status == ClaimStatus.CORROBORATED:
                corroborated.append(entry)
            elif result.status == ClaimStatus.SUPPORTED:
                supported.append(entry)
            elif result.status == ClaimStatus.PARTIAL:
                partial.append(entry)
            elif result.status == ClaimStatus.CONTRADICTED:
                contradicted.append(entry)
            else:
                unknown.append(entry)
        
        # Determine confidence level
        if corroborated:
            confidence = "high"
            primary = corroborated
        elif supported and not contradicted:
            confidence = "medium"
            primary = supported
        elif partial:
            confidence = "low"
            primary = partial
        else:
            confidence = "unknown"
            primary = []
        
        # Build answer text
        if primary:
            answer_lines = [primary[0]["text"]]
            if len(primary) > 1:
                answer_lines.append(f"\nAdditional supporting evidence: {len(primary) - 1} claims")
        else:
            answer_lines = ["Evidence is insufficient or contradictory."]
        
        answer = "\n".join(answer_lines)
        
        # Build evidence chain
        evidence_chain = []
        for claim, result in run.verified_claims:
            for cert in result.supporting_evidence:
                obs = next(
                    (o for o in run.observations if o.observation_id == cert.observation_id),
                    None,
                )
                if obs:
                    evidence_chain.append({
                        "claim": claim.text,
                        "source_url": obs.source_url,
                        "evidence_text": cert.span_text,
                        "retrieved_at": obs.observed_at.isoformat(),
                    })
        
        return SynthesisResult(
            question=run.contract.question,
            answer=answer,
            confidence=confidence,
            supported_by=tuple(c["text"][:50] for c in corroborated),
            qualified_by=tuple(c["text"][:50] for c in supported + partial),
            contradicted_by=tuple(c["text"][:50] for c in contradicted),
            unknown_aspects=tuple(c["text"][:50] for c in unknown),
            evidence_chain=tuple(evidence_chain),
        )
