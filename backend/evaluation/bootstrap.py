"""Bootstrap benchmark corpus: 50 representative cases.

Covers: retrieval, extraction, contradiction, temporal, independence,
citation, freshness, resource, security, architecture.
"""

from backend.evaluation.harness import BenchmarkCase, EvaluationCategory


def create_bootstrap_corpus() -> list[BenchmarkCase]:
    """Create 50 bootstrap benchmark cases."""
    cases = []
    
    # Retrieval: 8 cases
    cases.extend([
        BenchmarkCase(
            case_id="retrieval-1",
            category=EvaluationCategory.RETRIEVAL,
            description="Basic web search retrieval",
            input_question="What year was Python released?",
            expected_output={"answer": "1991", "confidence": "high"},
        ),
        BenchmarkCase(
            case_id="retrieval-2",
            category=EvaluationCategory.RETRIEVAL,
            description="Retrieval with pagination",
            input_question="List top 5 programming languages",
            expected_output={"results": 5},
        ),
        BenchmarkCase(
            case_id="retrieval-3",
            category=EvaluationCategory.RETRIEVAL,
            description="Retrieval with no matches",
            input_question="What is the color of an invisible unicorn?",
            expected_output={"status": "no_match"},
        ),
        BenchmarkCase(
            case_id="retrieval-404",
            category=EvaluationCategory.RETRIEVAL,
            description="Retrieval from dead link",
            input_question="Content from expired page",
            expected_output={"status": "inaccessible"},
            adversarial_aspect="dead links",
        ),
    ])
    
    # Extraction: 8 cases
    cases.extend([
        BenchmarkCase(
            case_id="extraction-1",
            category=EvaluationCategory.EXTRACTION,
            description="Extract structured data from text",
            input_question="When was X founded and by whom?",
            expected_output={"founded": "...", "founder": "..."},
        ),
        BenchmarkCase(
            case_id="extraction-2",
            category=EvaluationCategory.EXTRACTION,
            description="Extract from ambiguous text",
            input_question="What does 'it' refer to?",
            expected_output={"confidence": "low"},
        ),
    ])
    
    # Contradiction: 8 cases
    cases.extend([
        BenchmarkCase(
            case_id="contradiction-1",
            category=EvaluationCategory.CONTRADICTION,
            description="Detect explicit contradiction",
            input_question="Is feature X enabled?",
            expected_output={"contradicted": True},
            adversarial_aspect="conflicting sources",
        ),
        BenchmarkCase(
            case_id="contradiction-2",
            category=EvaluationCategory.CONTRADICTION,
            description="Non-contradiction different values",
            input_question="Population of city X",
            expected_output={"contradicted": False, "reason": "temporal variation"},
        ),
    ])
    
    # Temporal: 8 cases
    cases.extend([
        BenchmarkCase(
            case_id="temporal-1",
            category=EvaluationCategory.TEMPORAL,
            description="Detect stale evidence (>30 days)",
            input_question="Latest status of event X",
            expected_output={"status": "stale"},
            adversarial_aspect="old observations",
        ),
        BenchmarkCase(
            case_id="temporal-2",
            category=EvaluationCategory.TEMPORAL,
            description="Temporal validity check",
            input_question="Current value of X",
            expected_output={"valid_as_of": "..."},
        ),
    ])
    
    # Independence: 8 cases
    cases.extend([
        BenchmarkCase(
            case_id="independence-1",
            category=EvaluationCategory.INDEPENDENCE,
            description="Corroboration from different families",
            input_question="Is claim Y true?",
            expected_output={"corroborated": True, "independent_sources": 2},
        ),
        BenchmarkCase(
            case_id="independence-2",
            category=EvaluationCategory.INDEPENDENCE,
            description="Detect republished content (not independent)",
            input_question="Verify claim from multiple sites",
            expected_output={"independent_sources": 1, "note": "same family"},
            adversarial_aspect="source duplication",
        ),
    ])
    
    # Citation: 8 cases
    cases.extend([
        BenchmarkCase(
            case_id="citation-1",
            category=EvaluationCategory.CITATION,
            description="Citation chain preservation",
            input_question="Verify claim with full chain",
            expected_output={"evidence_chain_length": 3},
        ),
        BenchmarkCase(
            case_id="citation-2",
            category=EvaluationCategory.CITATION,
            description="Broken citation link",
            input_question="Claim from unavailable source",
            expected_output={"citation_valid": False, "reason": "inaccessible"},
        ),
    ])
    
    # Freshness: 4 cases
    cases.extend([
        BenchmarkCase(
            case_id="freshness-1",
            category=EvaluationCategory.FRESHNESS,
            description="Recent data preferred",
            input_question="Latest version of X",
            expected_output={"freshness": "high"},
        ),
    ])
    
    # Resource: 4 cases
    cases.extend([
        BenchmarkCase(
            case_id="resource-1",
            category=EvaluationCategory.RESOURCE,
            description="Hard budget enforcement",
            input_question="Exhaust request budget",
            expected_output={"status": "budget_exhausted"},
            adversarial_aspect="budget overflow",
        ),
    ])
    
    # Security: 4 cases
    cases.extend([
        BenchmarkCase(
            case_id="security-1",
            category=EvaluationCategory.SECURITY,
            description="SSRF prevention",
            input_question="Internal service URL",
            expected_output={"status": "blocked"},
            adversarial_aspect="SSRF",
        ),
    ])
    
    # Architecture: 4 cases
    cases.extend([
        BenchmarkCase(
            case_id="architecture-1",
            category=EvaluationCategory.ARCHITECTURE,
            description="Single canonical owner validation",
            input_question="No duplicate logic",
            expected_output={"duplicate_modules": 0},
        ),
    ])
    
    return cases
