from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "nightly-ai-research-20jobs.yml"
COLLECTOR = ROOT / "scripts" / "nightly_ai_research_job.sh"
REPORT = ROOT / "scripts" / "build_nightly_ai_research_report.js"


def test_expanded_20_job_workflow_has_seeded_and_qualified_matrix():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert text.count("seed_repos:") == 20
    matrix_rows = [
        line
        for line in text.splitlines()
        if 'id: "' in line and "seed_repos:" in line and "issues:" in line
    ]
    assert len(matrix_rows) == 20
    qualified = re.compile(r'issues: "((?:foundation|operations)#\\d+(?:,(?:foundation|operations)#\\d+)*)"')
    assert all(qualified.search(line) for line in matrix_rows)
    assert "PieroSierra/SecondBrain" in text
    assert "Shubhamsaboo/awesome-llm-apps" in text
    assert "NipunaRanasinghe/awesome-ai-agents" in text
    assert "modelcontextprotocol/quickstart-resources" in text
    assert "akullpp/awesome-java" in text
    assert "vinta/awesome-python" in text
    assert "ashishps1/awesome-system-design-resources" in text
    assert "ByteByteGoHq/system-design-101" in text
    assert "rafska/Awesome-local-LLM" in text


def test_research_collector_and_synthesis_scripts_are_syntactically_valid():
    bash = subprocess.run(["bash", "-n", str(COLLECTOR)], capture_output=True, text=True)
    assert bash.returncode == 0, bash.stderr
    node = subprocess.run(["node", "--check", str(REPORT)], capture_output=True, text=True)
    assert node.returncode == 0, node.stderr


def test_research_collector_records_seed_repository_provenance():
    text = COLLECTOR.read_text(encoding="utf-8")
    assert "SEED_REPOS" in text
    assert "github_seed_repositories.json" in text
    assert "github_seed_summary.json" in text
    assert "nightly-ai-research-observation/v3" in text
