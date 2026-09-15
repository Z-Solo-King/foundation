from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from benchmark.multi_agent import runner


def _args(output: Path, *, dry_run: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        start_slot=0,
        slots=1,
        output=str(output),
        dry_run=dry_run,
        global_capacity=20,
        compare=False,
    )


@pytest.mark.asyncio
async def test_live_mode_rejects_missing_executor_configuration(monkeypatch, tmp_path):
    monkeypatch.delenv("RESEARCH_LLM_ENDPOINT", raising=False)
    monkeypatch.delenv("RESEARCH_LLM_API_KEY", raising=False)
    monkeypatch.delenv("RESEARCH_LLM_MODEL", raising=False)

    with pytest.raises(RuntimeError, match="Live research executor is not configured"):
        await runner.run(_args(tmp_path / "live.jsonl"))


@pytest.mark.asyncio
async def test_dry_run_requires_explicit_flag_and_is_marked_completed(tmp_path):
    output = tmp_path / "dry.jsonl"
    await runner.run(_args(output, dry_run=True))

    rows = output.read_text(encoding="utf-8").splitlines()
    assert rows
    assert '"status": "completed"' in rows[0]
