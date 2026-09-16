from backend.api.models import ChatRequest


def test_chat_history_is_bounded_and_validated():
    request = ChatRequest(
        chat_id="c1",
        request_id="r1",
        message="hello",
        history=({"role": "user", "text": "previous"}, {"role": "assistant", "text": "answer"}),
    )
    request.validate()
    assert len(request.history) == 2


def test_chat_history_rejects_non_mapping_entry():
    request = ChatRequest(chat_id="c1", request_id="r1", message="hello", history=("not-a-mapping",))  # type: ignore[arg-type]
    try:
        request.validate()
    except ValueError as exc:
        assert "history entries" in str(exc)
    else:
        raise AssertionError("non-mapping history entry was accepted")


def test_chat_history_rejects_invalid_role():
    request = ChatRequest(chat_id="c1", request_id="r1", message="hello", history=({"role": "tool", "text": "x"},))
    try:
        request.validate()
    except ValueError as exc:
        assert "history role" in str(exc)
    else:
        raise AssertionError("invalid history role was accepted")


def test_chat_history_rejects_empty_text():
    request = ChatRequest(chat_id="c1", request_id="r1", message="hello", history=({"role": "user", "text": ""},))
    try:
        request.validate()
    except ValueError as exc:
        assert "history text" in str(exc)
    else:
        raise AssertionError("empty history text was accepted")


def test_chat_history_rejects_oversized_text():
    request = ChatRequest(chat_id="c1", request_id="r1", message="hello", history=({"role": "user", "text": "x" * 12001},))
    try:
        request.validate()
    except ValueError as exc:
        assert "history text" in str(exc)
    else:
        raise AssertionError("oversized history text was accepted")


def test_chat_history_rejects_more_than_twenty_turns():
    history = tuple({"role": "user", "text": str(i)} for i in range(21))
    request = ChatRequest(chat_id="c1", request_id="r1", message="hello", history=history)
    try:
        request.validate()
    except ValueError as exc:
        assert "history" in str(exc)
    else:
        raise AssertionError("oversized history was accepted")
