from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmark.ai_agent_benchmark_contract import validate_manifest


def test_ai_agent_benchmark_manifest_is_valid() -> None:
    payload = json.loads((ROOT / "benchmark" / "ai_agent_task_matrix_v1.json").read_text(encoding="utf-8"))
    assert validate_manifest(payload) == []
