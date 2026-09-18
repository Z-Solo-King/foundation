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


_ALLOWED_SYNTHESIS_STATUSES = frozenset({
    ClaimStatus.CORROBORATED,
    ClaimStatus.SUPPORTED,
    ClaimStatus.PARTIAL,
    ClaimStatus.CONTRADICTED,
    ClaimStatus.UNKNOWN,
    ClaimStatus.INACCESSIBLE,
    ClaimStatus.STALE,
    ClaimStatus.INFERRED,
})


@dataclass(frozen=True)
class SynthesisClaimProjection:
    claim_id: str
    text: str
    status: str
    evidence_ids: tuple[str, ...] = ()
    qualifier: str = ""

    def validate(self) -> None:
        if not self.claim_id.strip() or not self.text.strip():
            raise ValueError("synthesis claim identity and text are required")
        if self.status not in _ALLOWED_SYNTHESIS_STATUSES:
            raise ValueError("unsupported synthesis claim status")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("synthesis evidence IDs must be unique")
        if self.status in {ClaimStatus.CORROBORATED, ClaimStatus.SUPPORTED} and not self.evidence_ids:
            raise ValueError("supported synthesis claims require evidence")
        if self.status == ClaimStatus.PARTIAL and not self.qualifier.strip():
            raise ValueError("partial synthesis claims require a qualifier")


@dataclass(frozen=True)
class SynthesisProjection:
    question: str
    claims: tuple[SynthesisClaimProjection, ...]
    gaps: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.question.strip():
            raise ValueError("synthesis question is required")
        ids = [claim.claim_id for claim in self.claims]
        if len(ids) != len(set(ids)):
            raise ValueError("synthesis claim IDs must be unique")
        for claim in self.claims:
            claim.validate()
        if any(not gap.strip() for gap in self.gaps):
            raise ValueError("synthesis gaps must be non-empty")


def build_synthesis_projection(verified_claims, *, question: str, required_claim_ids: tuple[str, ...] = ()) -> SynthesisProjection:
    if not question.strip():
        raise ValueError("synthesis question is required")
    if len(set(required_claim_ids)) != len(required_claim_ids):
        raise ValueError("required claim IDs must be unique")
    projections = []
    gaps = []
    for claim, result in verified_claims:
        claim_id = str(getattr(claim, "claim_id", "") or "")
        text = str(getattr(claim, "text", "") or "")
        status = str(getattr(result, "status", ClaimStatus.UNKNOWN) or ClaimStatus.UNKNOWN)
        if not claim_id or not text:
            raise ValueError("verified claim projection requires claim identity and text")
        supporting = tuple(
            str(getattr(certificate, "observation_id", "") or "")
            for certificate in getattr(result, "supporting_evidence", ())
            if str(getattr(certificate, "observation_id", "") or "")
        )
        if status in {ClaimStatus.CORROBORATED, ClaimStatus.SUPPORTED}:
            projections.append(SynthesisClaimProjection(claim_id, text, status, supporting))
        elif status == ClaimStatus.PARTIAL:
            projections.append(SynthesisClaimProjection(
                claim_id,
                text,
                status,
                supporting,
                "This claim is only partially supported by the available evidence.",
            ))
        elif status in {
            ClaimStatus.CONTRADICTED, ClaimStatus.UNKNOWN, ClaimStatus.INACCESSIBLE,
            ClaimStatus.STALE, ClaimStatus.INFERRED,
        }:
            gaps.append(claim_id)
        else:
            raise ValueError("verified claim has unsupported status")
    present_ids = {claim.claim_id for claim in projections} | set(gaps)
    if sorted(set(required_claim_ids) - present_ids):
        raise ValueError("required verified claims are missing")
    projection = SynthesisProjection(question, tuple(projections), tuple(gaps))
    projection.validate()
    return projection


def _projection_answer(projection: SynthesisProjection) -> str:
    parts = []
    for claim in projection.claims:
        if claim.status == ClaimStatus.PARTIAL:
            parts.append(f"{claim.qualifier} {claim.text}")
        else:
            parts.append(claim.text)
    if projection.gaps:
        parts.append("Unresolved aspects: " + "; ".join(projection.gaps))
    return "
".join(parts) if parts else "Evidence is insufficient to answer this question."

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
        projection = build_synthesis_projection(run.verified_claims, question=question)
        return SynthesisResult(
            question=question,
            answer=_projection_answer(projection),
            confidence=_confidence(buckets),
            supported_by=tuple(claim.claim_id for claim, _ in buckets["corroborated"]),
            qualified_by=tuple(claim.claim_id for claim, _ in buckets["supported"] + buckets["partial"]),
            contradicted_by=tuple(claim.claim_id for claim, _ in buckets["contradicted"]),
            unknown_aspects=tuple(claim.claim_id for claim, _ in buckets["unknown"]),
            evidence_chain=_evidence_chain(run),
        )
