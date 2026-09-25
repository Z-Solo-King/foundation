from __future__ import annotations
import json
from pathlib import Path
from benchmark.ai_agent_benchmark_contract import validate_manifest
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"benchmark"/"ai_agent_task_matrix_v1.json"
def test_ai_agent_benchmark_manifest_is_valid():
    assert validate_manifest(json.loads(MANIFEST.read_text(encoding="utf-8"))) == []
