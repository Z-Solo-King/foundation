from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "nightly-ai-research-20jobs.yml"
COLLECTOR = ROOT / "scripts" / "nightly_ai_research_job.sh"
REPORT = ROOT / "scripts" / "build_nightly_ai_research_report.js"
AUTONOMOUS_WORKFLOW = ROOT / ".github" / "workflows" / "autonomous-benchmark.yml"


def test_expanded_20_job_workflow_has_seeded_and_qualified_matrix():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert text.count("seed_repos:") == 20
    matrix_rows = [
        line
        for line in text.splitlines()
        if 'id: "' in line and "seed_repos:" in line and "issues:" in line
    ]
    assert len(matrix_rows) == 20
    issue_fields = [re.search(r'issues: "([^"]+)"', line) for line in matrix_rows]
    assert all(match for match in issue_fields)
    assert all(
        all(part.startswith(("foundation#", "operations#")) for part in match.group(1).split(","))
        for match in issue_fields
    )
    assert "PieroSierra/SecondBrain" in text
    assert "Shubhamsaboo/awesome-llm-apps" in text
    assert "NipunaRanasinghe/awesome-ai-agents" in text
    assert "modelcontextprotocol/quickstart-resources" in text
    assert "akullpp/awesome-java" in text
    assert "vinta/awesome-python" in text
    assert "ashishps1/awesome-system-design-resources" in text
    assert "ByteByteGoHq/system-design-101" in text
    assert "rafska/Awesome-local-LLM" in text
    assert "foundation#154" not in text


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


def test_autonomous_benchmark_consumes_latest_research_feed():
    text = AUTONOMOUS_WORKFLOW.read_text(encoding="utf-8")
    assert "research_feed:" in text
    assert "nightly-ai-research-20jobs.yml" in text
    assert "latest-research-feed" in text
    assert "research-feed-status/v1" in text
