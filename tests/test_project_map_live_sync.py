from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_project_map_live_sync_snapshot_is_structurally_consistent():
    data = json.loads((ROOT / "docs" / "AI_PROJECT_MAP.json").read_text(encoding="utf-8"))

    source_head = data["source_head_at_generation"]
    assert re.fullmatch(r"[0-9a-f]{40}", source_head)

    live = data["live_synchronization"]
    assert live["foundation_main"] == source_head
    assert re.fullmatch(r"[0-9a-f]{40}", live["operations_main"])
    assert re.fullmatch(r"[0-9a-f]{40}", live["production_operations_revision"])

    for prefix in ("foundation", "operations"):
        issues = live[f"{prefix}_open_issues"]
        prs = live[f"{prefix}_open_prs"]
        assert len(issues) == live[f"{prefix}_open_issue_count"]
        assert len(prs) == live[f"{prefix}_open_pr_count"]
        assert all(isinstance(item, int) and item > 0 for item in issues + prs)

    extractor = data["extractor_mapper_status"]
    assert extractor["standalone_repository_status"] == "retired/deleted"
    assert extractor["operations_private_runtime_path"] == "operations/extractor_mapper/"
    assert "foundation_core.product_mapping" in extractor["public_mapper_authority"]
