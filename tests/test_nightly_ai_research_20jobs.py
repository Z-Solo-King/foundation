from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "nightly-ai-research-20jobs.yml"
COLLECTOR = ROOT / "scripts" / "nightly_ai_research_job.sh"
REPORT = ROOT / "scripts" / "build_nightly_ai_research_report.js"
AUTONOMOUS_WORKFLOW = ROOT / ".github" / "workflows" / "autonomous-benchmark.yml"


def test_public_20_job_workflow_is_paused():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "schedule:" not in text
    assert "push:" not in text
    assert "task workflow is paused" in text

def test_research_collector_and_synthesis_scripts_are_syntactically_valid():
    bash = subprocess.run(["bash", "-n", str(COLLECTOR)], capture_output=True, text=True)
    assert bash.returncode == 0, bash.stderr
    node = subprocess.run(["node", "--check", str(REPORT)], capture_output=True, text=True)
    assert node.returncode == 0, node.stderr
    report_text = REPORT.read_text(encoding="utf-8")
    assert "family_graph_sha256" in report_text
    assert "family_graph_digest_count" in report_text
    assert "stale_benchmark_targets" in report_text


def test_research_collector_records_seed_repository_provenance():
    text = COLLECTOR.read_text(encoding="utf-8")
    assert "SEED_REPOS" in text
    assert "github_seed_repositories.json" in text
    assert "github_seed_summary.json" in text
    assert "nightly-ai-research-observation/v3" in text
    assert "FAMILY_INTEGRATION_GRAPH.json" in text
    assert "family_graph_sha256" in text


def test_research_report_produces_deterministic_signal_candidates():
    text = REPORT.read_text(encoding="utf-8")
    assert "buildSignalCandidates" in text
    assert 'signal_candidates: signalCandidates' in text
    assert 'evidence_class:"research-signal"' in text


def test_autonomous_benchmark_workflow_is_paused():
    text = AUTONOMOUS_WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "schedule:" not in text
    assert "push:" not in text
    assert "task workflow is paused" in text

def test_family_integrity_normalizes_issue_targets_before_comparison():
    checker = (ROOT / "scripts" / "family_integrity_check.js").read_text(encoding="utf-8")
    assert "normalizeIssueNumbers" in checker
    assert "normalizeIssueKeys" in checker


def test_nightly_preflight_preserves_network_failure_receipt_without_parse_crash():
    text = (ROOT / ".github" / "workflows" / "nightly-research-provider-preflight.yml").read_text(encoding="utf-8")
    probe = (ROOT / "scripts" / "nightly_runtime_contract_probe.py").read_text(encoding="utf-8")
    assert "probe_transport_error" in probe
    assert "runtime_revision_mismatch" in probe
    assert "invalid_json_response" in probe


def test_nightly_diagnosis_synthesizes_cancelled_research_lanes_without_masking_unexpected_missing_artifacts():
    text = (ROOT / '.github' / 'workflows' / 'nightly-multi-agent-research-v3.yml').read_text(encoding='utf-8')
    assert 'research_result = "${{ needs.research.result }}"' in text
    assert "research_result in {'cancelled', 'skipped'}" in text
    assert "'state': 'blocked_before_execution'" in text
    assert 'raise FileNotFoundError(path)' in text


def test_nightly_workflow_has_one_canonical_summary_and_final_gate():
    workflow = (ROOT / '.github' / 'workflows' / 'nightly-multi-agent-research-v3.yml').read_text(encoding='utf-8')
    assert workflow.count('  project-summary:') == 1
    assert workflow.count('  final-gate:') == 1
    assert workflow.count('      - name: Build truthful nightly diagnosis') == 1
    assert workflow.count('          research_result = "${{ needs.research.result }}"') == 1
    assert ' + \'{{' not in workflow


def test_nightly_workflow_handles_cancelled_research_without_masking_unexpected_missing_artifacts():
    workflow = (ROOT / '.github' / 'workflows' / 'nightly-multi-agent-research-v3.yml').read_text(encoding='utf-8')
    assert "research_result in {'cancelled', 'skipped'}" in workflow
    assert "'state': 'blocked_before_execution'" in workflow
    assert 'raise FileNotFoundError(path)' in workflow
    assert "'artifact_missing': True" in workflow