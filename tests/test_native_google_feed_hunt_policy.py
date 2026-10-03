import pathlib


WORKFLOW = pathlib.Path(".github/workflows/native-google-feed-hunt.yml")


def test_explicit_cross_origin_feed_policy_is_preserved():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'local candidate="$1"' in text
    assert 'same_host "$linked_final" "$u"' in text
    assert "path_guess" in text
    assert "directory_index_link" in text
    assert "explicit_page_reference" in text
    assert '[ "$(same_host "$u")" = "1" ] || continue' not in text


def test_guess_redirects_remain_same_host_only():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert '[ "$(same_host "$final")" = "1" ]' in text
