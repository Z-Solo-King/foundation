import pathlib

WORKFLOW = pathlib.Path(".github/workflows/native-google-feed-hunt.yml")


def test_explicit_cross_origin_feed_policy_is_preserved():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'local candidate="$1"' in text
    assert 'local base="$root"' in text
    assert "resolve_url()" in text
    assert "public_url()" in text
    assert "fetch_public()" in text
    assert 'same_host "$linked_final" "$u"' in text
    assert "path_guess" in text
    assert "directory_index_link" in text
    assert "explicit_page_reference" in text
    assert '[ "$(same_host "$u")" = "1" ] || continue' not in text


def test_feed_redirects_are_host_pinned_and_public_validated():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "public_url \"$u\" || return 1" in text
    assert 'same_host "$linked_final" "$u"' in text


def test_guess_paths_remain_same_host_only():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'same_host "$final")" = "1"' in text
