from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "hybrid-language-pilots.yml"


def test_pinned_foundation_reference_checkouts_use_manual_sha_fetch():
    text = WORKFLOW.read_text(encoding="utf-8")
    exact_block = text[text.index("name: Checkout exact pinned Foundation public core"):text.index("name: Materialize pinned public foundation_core", text.index("name: Checkout exact pinned Foundation public core"))]
    assert "ref: ${{ steps.foundation-core-pin.outputs.ref }}" not in exact_block
    assert 'git fetch --no-tags --depth=1 origin "$FOUNDATION_COMMIT"' in exact_block
    assert 'git checkout --detach "$FOUNDATION_COMMIT"' in exact_block


def test_url_reference_uses_foundation_backend_source_not_removed_operations_backend():
    text = WORKFLOW.read_text(encoding="utf-8")
    start = text.index("name: Rust URL canonicalization Python differential")
    block = text[start:text.index("name: Rust URL identity 32x3 benchmark", start)]
    assert "foundation-url-ref" in block
    assert "foundation-reference" in block
    assert "backend/sources/http.py" in block
    assert "PYTHONPATH: ${{ github.workspace }}/foundation-reference" in block
    assert "pip install --disable-pip-version-check -e operations" not in block
