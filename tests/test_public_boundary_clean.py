from pathlib import Path
import asyncio
from types import SimpleNamespace


def test_public_worker_routes_are_exact_and_chat_errors_redacted():
    text = (Path(__file__).resolve().parents[1] / "worker.py").read_text(encoding="utf-8")
    assert 'path == "/health"' in text
    assert 'path.endswith("/health")' not in text
    assert 'path == "/api/v1/chat"' in text
    assert 'path.endswith("/api/v1/chat")' not in text
    assert 'path.startswith("/api/v1/research/") and path.count("/") == 4' in text
    assert '"error_detail": str(exc)' not in text


def test_public_chat_response_projection_is_present():
    text = (Path(__file__).resolve().parents[1] / "worker.py").read_text(encoding="utf-8")
    assert "_PUBLIC_CHAT_TOP_LEVEL_FIELDS" in text
    assert "_PUBLIC_CHAT_RESPONSE_FIELDS" in text
    assert "_public_chat_body" in text


def test_public_research_fetch_and_storage_errors_are_stable_codes():
    worker = (Path(__file__).resolve().parents[1] / "worker.py").read_text(encoding="utf-8")
    research = (Path(__file__).resolve().parents[1] / "backend" / "worker_research.py").read_text(encoding="utf-8")
    assert '"persistence_unavailable"' in worker
    assert '"source_fetch_failed"' in research
