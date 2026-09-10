"""Thin research UI for contract submission and result inspection.

No business logic here. Delegates all decisions to backend.intelligence
and backend.execution layers.
"""

import json
from dataclasses import asdict
from typing import Any

from backend.api.models import ResearchRequest, APIResponse
from backend.api.main import submit_research, health_endpoint, readiness_endpoint
from backend.execution.engine import ResearchRun, summarize_research
from backend.execution.synthesis import ResearchSynthesizer


class ResearchUI:
    """Thin UI layer for research submission and results."""
    
    def __init__(self):
        self.synthesizer = ResearchSynthesizer()
    
    def render_health_check(self) -> dict[str, Any]:
        """Render /health endpoint."""
        return health_endpoint()
    
    def render_readiness_check(self) -> dict[str, Any]:
        """Render /readiness endpoint."""
        return readiness_endpoint()
    
    def render_research_form(self) -> dict[str, Any]:
        """Render research submission form schema."""
        return {
            "title": "Research Intelligence Engine",
            "description": "Submit a research question for evidence-based investigation",
            "form": {
                "question": {
                    "type": "text",
                    "required": True,
                    "placeholder": "What would you like to research?",
                },
                "depth": {
                    "type": "select",
                    "options": ["quick", "standard", "deep"],
                    "default": "standard",
                },
                "require_citations": {
                    "type": "checkbox",
                    "default": True,
                },
                "max_sources": {
                    "type": "number",
                    "default": 20,
                    "min": 1,
                },
                "max_evidence_items": {
                    "type": "number",
                    "default": 100,
                    "min": 1,
                },
            },
        }
    
    def submit_research(
        self,
        question: str,
        depth: str = "standard",
        require_citations: bool = True,
        max_sources: int = 20,
        max_evidence_items: int = 100,
    ) -> dict[str, Any]:
        """Submit a research request.
        
        Args:
            question: Research question
            depth: quick, standard, or deep
            require_citations: Whether to require citations
            max_sources: Maximum sources to use
            max_evidence_items: Maximum evidence observations
            
        Returns:
            Response dict with run_id or error
        """
        request = ResearchRequest(
            question=question,
            depth=depth,
            require_citations=require_citations,
            max_sources=max_sources,
            max_evidence_items=max_evidence_items,
            strict_zero_cost_only=True,
        )
        
        response = submit_research(request)
        return asdict(response)
    
    def render_run_summary(self, run: ResearchRun) -> dict[str, Any]:
        """Render run summary for UI.
        
        Args:
            run: Completed ResearchRun
            
        Returns:
            Rendered summary dict
        """
        summary = summarize_research(run)
        return {
            "run_id": summary["run_id"],
            "status": summary["status"],
            "question": summary["question"],
            "observations_count": summary["observations"],
            "claims_verified": summary["claims_verified"],
            "corroborated": summary["corroborated_claims"],
            "contradicted": summary["contradicted_claims"],
            "findings": summary["findings"],
        }
    
    def render_synthesis_result(self, run: ResearchRun) -> dict[str, Any]:
        """Render synthesis result for user.
        
        Args:
            run: Completed ResearchRun
            
        Returns:
            User-facing result with citations
        """
        result = self.synthesizer.synthesize(run)
        
        return {
            "question": result.question,
            "answer": result.answer,
            "confidence": result.confidence,
            "summary": {
                "supported_by": len(result.supported_by),
                "qualified_by": len(result.qualified_by),
                "contradicted_by": len(result.contradicted_by),
                "unknown_aspects": len(result.unknown_aspects),
            },
            "evidence_chain": [
                {
                    "claim": e["claim"],
                    "source": e["source_url"],
                    "quote": e["evidence_text"],
                    "retrieved": e["retrieved_at"],
                }
                for e in result.evidence_chain
            ],
        }
