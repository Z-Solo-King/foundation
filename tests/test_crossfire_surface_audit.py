from pathlib import Path

import json
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def audit_result(tmp_path):
    output = tmp_path / "crossfire-audit.json"
    completed = subprocess.run(
        [sys.executable, str(ROOT / "tools/crossfire_surface_audit.py"), "--root", str(ROOT), "--output", str(output)],
        cwd=ROOT, text=True, capture_output=True
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return json.loads(output.read_text(encoding="utf-8"))


def test_crossfire_automation_policy_covers_every_project_component():
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        result = audit_result(Path(directory))
    assert result["passed"] is True
    assert result["component_count"] >= 10
    assert result["missing_workflows"] == {}


def test_crossfire_policy_is_adaptive_bounded_and_advisory():
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        result = audit_result(Path(directory))
    policy = result["policy"]
    assert policy["target_ai_lanes"] == 6
    assert policy["strong_ai_lane_threshold"] == 5
    assert policy["adaptive_ai_lane_counts"] == [0, 2, 4, 6]
    assert policy["deterministic_lenses"] == [
        "structure",
        "boundary",
        "runtime",
        "security",
        "quality",
        "provenance",
    ]
    assert policy["independence"] is True
    assert policy["shared_result_feedback"] is False


def test_crossfire_coverage_gate_is_automated():
    workflow = (ROOT / ".github/workflows/crossfire-coverage-gate.yml").read_text(encoding="utf-8")
    assert "crossfire_surface_audit.py" in workflow
    assert "python -m pytest -q tests/test_crossfire_workflows.py tests/test_crossfire_surface_audit.py" in workflow
    assert "schedule:" in workflow
