    assert '"note"' in text
    assert "private/chatbot/chat_endpoint.py" in text
    assert "private/chatbot/live_answer.py" in text


def test_post_nightly_canary_uses_same_structured_research_contract():
    text=(Path(__file__).parents[1] / ".github" / "workflows" / "live-nightly-research-canary.yml").read_text(encoding="utf-8")
    assert "research_agent:true" not in text
    assert '"X-Heroic-Research-Proof: 1"' in text
    assert 'has("findings")' in text
    assert 'has("follow_up_questions")' in text
    assert 'has("note")' in text
    assert "fromjson" in text


def test_run_name_distinguishes_live_and_contract_only_runs():
    text=workflow_text()
    assert "run-name: >-" in text
    assert "scheduled-live" in text
    assert "contract-dry-run" in text
    assert "production-live" in text


def test_canary_manual_execution_is_main_only_and_post_nightly_main_only():
    text=(Path(__file__).parents[1] / ".github" / "workflows" / "live-nightly-research-canary.yml").read_text(encoding="utf-8")
    assert "github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main'" in text
    assert "github.event.workflow_run.head_branch == 'main'" in text