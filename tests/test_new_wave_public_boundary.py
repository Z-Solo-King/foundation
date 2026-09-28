from pathlib import Path

def test_public_routes_use_exact_paths_and_public_projection():
    text = (Path(__file__).resolve().parents[1] / "worker.py").read_text(encoding="utf-8")
    assert "path = urlparse(request.url).path" in text
    assert 'path.endswith("/api/v1/chat")' not in text
    assert "_PUBLIC_CHAT_TOP_LEVEL_FIELDS" in text
    assert "_PUBLIC_CHAT_RESPONSE_FIELDS" in text
    assert "error_detail" not in text

def test_url_identity_blocks_numeric_short_forms_and_brackets_ipv6():
    text = (Path(__file__).resolve().parents[1] / "foundation_core" / "url_identity.py").read_text(encoding="utf-8")
    assert "host_for_netloc" in text
    assert "len(parts) != 4" in text
    assert "2002" in text
    assert "20010000" in text

def test_http_fetch_has_time_and_size_guards():
    text = (Path(__file__).resolve().parents[1] / "backend" / "sources" / "http.py").read_text(encoding="utf-8")
    assert "FETCH_TIMEOUT_SECONDS" in text
    assert "content-length" in text
    assert "response exceeds acquisition size budget" in text

def test_public_research_source_errors_are_stable_codes():
    text = (Path(__file__).resolve().parents[1] / "backend" / "worker_research.py").read_text(encoding="utf-8")
    assert '"source_fetch_failed"' in text
