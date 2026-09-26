from pathlib import Path

from scripts.publish_benchmark_findings import TRACKING_LABEL, TRACKING_TITLE, build_issue_body, collect_findings

def test_instruction_finding_becomes_issue_candidate():
    report = {"schema": "instruction-audit/v1", "finding_count": 1, "findings": [{"kind": "duplicate", "document": "AGENTS.md", "line": 4, "detail": "matches CLAUDE.md:7"}]}
    findings = collect_findings(report, None)
    assert len(findings) == 1
    body = build_issue_body(findings, "123", "Z-Solo-King/foundation")
    assert "# Automated benchmark findings" in body
    assert TRACKING_TITLE == "Nightly benchmark findings — automated tracking"
    assert TRACKING_LABEL == "benchmark-finding"
    assert "does not authorize policy" in body

def test_benchmark_hard_gate_failure_is_consumed():
    findings = collect_findings(None, {"hard_gate_failures": ["security"]})
    assert findings[0]["kind"] == "hard-gate-failure"

def test_normal_benchmark_report_has_no_finding():
    report = {"hard_gate_rule": "numeric observations never override security/policy/provenance/runtime/production gates"}
    assert collect_findings(None, report) == []

def test_workflow_reference_exists():
    workflow = Path(".github/workflows/nightly-ai-research-20jobs.yml").read_text(encoding="utf-8")
    assert "issues: write" in workflow
    assert "scripts/publish_benchmark_findings.py" in workflow
