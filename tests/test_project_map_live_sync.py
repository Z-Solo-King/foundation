from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_public_safe_project_map_tracks_live_state_and_extractor_authority():
    data = json.loads((ROOT / "docs/AI_PROJECT_MAP.json").read_text(encoding="utf-8"))
    assert data["source_head_at_generation"] == "6adee271c0fffa9dbac5b2af001bb9351f8db9a8"
    status = data["extractor_mapper_status"]
    assert status["standalone_repository_status"] == "retired/deleted"
    assert "foundation_core.product_mapping" in status["public_mapper_authority"]
    live = data["live_synchronization"]
    assert live["foundation_main"] == "6adee271c0fffa9dbac5b2af001bb9351f8db9a8"
    assert live["foundation_open_issue_count"] == 4
    assert set(live["foundation_open_prs"]).issuperset({1616, 1606, 1604, 1602, 1575, 1558})
