"""Project README with architecture overview and quickstart."""

# Research Intelligence Engine — Zero-Dollar Personal Research System

## Mission

Build a private, durable, evidence-first research intelligence engine that:
- Researches across web, communities, files, code, media, and structured artifacts through permitted access paths
- Preserves durable observations, evidence spans, document versions, source lineage, and claim relationships
- Distinguishes unknown, inaccessible, contradictory, stale, partial, inferred, and supported states
- Operates at **strict $0/month runtime** with no paid dependencies
- Remains functional when external AI services are unavailable

## Architecture

### Core Layers

```
Client/UI
   ↓
HTTP API (backend/api)
   ↓
Planner (backend/intelligence/planning)
   ↓
Acquisition (backend/execution/acquisition)
   ↓
Observations (backend/intelligence/observations)
   ↓
Evidence Mapper (backend/intelligence/verifier)
   ↓
Verification (contradiction, independence, staleness)
   ↓
Synthesis (backend/execution/synthesis)
   ↓
User-Facing Result
```

### Persistence

- **D1 (Metadata)**: Run state, evidence graph, source lineage, document versions
- **R2 (Artifacts)**: Raw documents, PDFs, media, extracted content
- **In-Memory (Testing)**: Full database simulation

### Execution Model

- **Research Run**: Contract → Plan → Observations → Claims → Verification → Synthesis
- **Resource Budgets**: Hard envelopes on requests, evidence items, inference calls
- **Provider Router**: Free-tier eligibility gates; no overspend
- **Public Worker Boundary**: Nonce, schema, hash validation; fail-closed; untrusted

### Evidence Model

**Canonical provenance path:**
```
Claim → EvidenceSpan → EvidenceCertificate → Observation → Source → SourceFamily → SourceLineage
```

**Claim states (explicit):**
- SUPPORTED: Evidence from one source family
- CORROBORATED: Evidence from multiple independent families
- CONTRADICTED: Conflicting evidence
- UNKNOWN: No evidence found
- INACCESSIBLE: Sources unreachable
- STALE: Evidence >30 days old
- PARTIAL: Mixed old/new or contradictory evidence
- INFERRED: Derived from other claims

## Features

### Phase 0-1: Production Core (✅ Complete)
- [x] Repository consolidation (removed payload duplicate)
- [x] Contract hardening (Research, Resource, Capability contracts)
- [x] HTTP API surface (health, readiness, submit)
- [x] D1/R2 persistence layer
- [x] Evidence verifier (contradiction, independence, staleness)
- [x] Provider router with free-eligibility gates

### Phase 2-3: Execution Pipeline (✅ Complete)
- [x] Research execution engine (run lifecycle)
- [x] Synthesis layer (confidence scoring, citations)
- [x] Acquisition executor (source policies, lineage)
- [x] Public worker boundary (nonce, hash, replay validation)
- [x] Evaluation harness (50-case bootstrap, 150+ production gate)

### Phase 4-5: Learning & UI (✅ Complete)
- [x] Research UI (form, submission, results rendering)
- [x] Promotion gate (shadow/canary/rollback infrastructure)
- [x] Bootstrap benchmark corpus (50 cases across 10 categories)

## Getting Started

### Installation

```bash
git clone https://github.com/Z-Solo-King/research-intelligence-engine-public
cd research-intelligence-engine-public
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running Tests

```bash
pytest tests/ -v
pytest tests/test_core_batch.py  # Core contracts
pytest tests/test_verifier.py    # Evidence verification
pytest tests/test_engine.py      # Execution pipeline
pytest tests/test_evaluation.py  # Evaluation harness
```

### Submitting Research

```python
from backend.api.main import submit_research
from backend.api.models import ResearchRequest

request = ResearchRequest(
    question="What is the history of Python?",
    depth="standard",
    require_citations=True,
)
response = submit_research(request)
print(response)
```

### Running a Complete Research Pipeline

```python
from backend.execution.engine import (
    create_run,
    start_research,
    add_observation,
    verify_and_add_claim,
    complete_research,
)
from backend.execution.synthesis import ResearchSynthesizer
from backend.intelligence.contracts import ResearchContract, ResearchPlan
from backend.intelligence.observations import Observation, EvidenceSpan
from backend.intelligence.certificates import create_certificate
from backend.intelligence.claims import Claim
from backend.intelligence.lineage import SourceLineage
from backend.intelligence.verifier import EvidenceVerifier
from backend.execution.resources import ResourceBudget

# Create run
contract = ResearchContract(question="What is X?")
plan = ResearchPlan(
    question="What is X?",
    stages=("discover", "collect", "verify", "synthesize"),
    source_budget=5,
    evidence_budget=10,
)
run = create_run("run-1", contract, plan)
run = start_research(run)

# Add observations
obs = Observation.create("o1", "s1", "https://example.com", "X is true.")
run = add_observation(run, obs, ResourceBudget(evidence_items=100))

# Verify claims
span = EvidenceSpan("o1", 0, 1)
cert = create_certificate(obs, span)
claim = Claim.create("c1", "X is true.")
lineage = SourceLineage("s1", "family-a")
verifier = EvidenceVerifier()
run = verify_and_add_claim(run, claim, (cert,), verifier, {"s1": lineage})

# Complete and synthesize
run = complete_research(run)
synthesizer = ResearchSynthesizer()
result = synthesizer.synthesize(run)
print(result)
```

## Policy & Constraints

### Immutable Protected Policy
- Privacy boundaries
- Security gates (SSRF, auth, CAPTCHAs)
- Retention requirements
- Billing/no-overage constraints
- Public/private repository boundary
- Evidence semantics and truth-state definitions

### Mutable Learning Domain
- Source ranking preferences
- Cache effectiveness
- Extractor variants
- Provider/capability routing heuristics
- Research query portfolio ordering
- Safe performance optimizations

## Cost Model

**Target: $0/month runtime**

- Cloudflare Workers: Free tier (100k requests/day)
- D1: Free tier (3GB database)
- R2: Free tier (10GB storage) + $0.015/GB after
- Caching: Deterministic operations cached locally
- AI: Optional; gates on free-tier providers only

## Development

### Adding a Test

```python
# tests/test_example.py
def test_my_feature():
    """Description of what this tests."""
    # Arrange
    fixture = setup()
    
    # Act
    result = do_something(fixture)
    
    # Assert
    assert result == expected
```

### Architecture Conformance

Before committing:
1. **No duplicates**: Ensure each behavior has one canonical owner
2. **Policy gates**: Check that security/privacy/billing gates are enforced
3. **Evidence chain**: Verify claim → cert → obs → source provenance
4. **Resource budgets**: Confirm all external calls respect budgets
5. **Tests pass**: `pytest tests/ -v`

## Security & Privacy

- Public workers are untrusted; all outputs fail-closed validated
- Private evidence graph never exposed to public compute
- Replay prevention via nonce tracking
- Hash integrity checks on all artifacts
- No SSRF, auth bypass, or access-control bypass
- Retention policies enforced at R2 layer

## References

- **Architecture Doc**: See `ARCHITECTURE.md` (in private repo)
- **Implementation Plan**: See `COPILOT_PLAN.md` (in private repo)
- **Bootstrap Benchmark**: 50 cases in `backend/evaluation/bootstrap.py`
- **API Spec**: Implicit in `backend/api/main.py` and models

## License

Private research project. No external distribution.
