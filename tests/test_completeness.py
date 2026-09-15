import pytest

from backend.intelligence.completeness import (
    CompletenessStatus,
    PageObservation,
    PaginationMode,
    certify_completeness,
)


def page(number, items=10, **kwargs):
    return PageObservation(page_id=f"p-{number}", sequence=number, item_count=items, **kwargs)


def test_page_number_explicit_end_is_complete():
    receipt = certify_completeness(
        (page(1), page(2, next_url=None)),
        mode=PaginationMode.PAGE_NUMBER,
        termination_reason="explicit_end",
    )
    assert receipt.certified_complete
    assert receipt.pages_visited == 2
    assert receipt.items_observed == 20


def test_cursor_exhaustion_is_complete():
    receipt = certify_completeness(
        (page(1, next_token="cursor-2"), page(2)),
        mode=PaginationMode.CURSOR,
        termination_reason="cursor_exhausted",
    )
    assert receipt.completeness == CompletenessStatus.COMPLETE
    assert receipt.next_page_observed


def test_missing_next_link_is_partial_not_complete():
    receipt = certify_completeness(
        (page(1),),
        mode=PaginationMode.NEXT_LINK,
        termination_reason="missing_next_link",
    )
    assert receipt.completeness == CompletenessStatus.PARTIAL
    assert not receipt.certified_complete


def test_repeated_page_is_partial():
    receipt = certify_completeness(
        (page(1), page(2, content_digest="same")),
        mode=PaginationMode.INFINITE_SCROLL,
        termination_reason="repeated_page",
    )
    assert receipt.completeness == CompletenessStatus.PARTIAL


def test_blocked_always_wins_over_termination_reason():
    receipt = certify_completeness(
        (page(1),),
        mode=PaginationMode.PAGE_NUMBER,
        termination_reason="explicit_end",
        blocked=True,
    )
    assert receipt.completeness == CompletenessStatus.BLOCKED
    assert not receipt.certified_complete


def test_unavailable_is_distinct_from_unknown():
    receipt = certify_completeness(
        (),
        mode=PaginationMode.CURSOR,
        termination_reason="transport_failure",
        unavailable=True,
    )
    assert receipt.completeness == CompletenessStatus.UNAVAILABLE


def test_no_pages_are_unknown():
    receipt = certify_completeness(
        (),
        mode=PaginationMode.PAGE_NUMBER,
        termination_reason="not_started",
    )
    assert receipt.completeness == CompletenessStatus.UNKNOWN


def test_invalid_page_sequence_rejected():
    with pytest.raises(ValueError):
        certify_completeness(
            (page(1), page(3)),
            mode=PaginationMode.PAGE_NUMBER,
            termination_reason="explicit_end",
        )


def test_duplicate_page_id_rejected():
    with pytest.raises(ValueError):
        certify_completeness(
            (page(1), PageObservation(page_id="p-1", sequence=2, item_count=2)),
            mode=PaginationMode.PAGE_NUMBER,
            termination_reason="explicit_end",
        )


def test_invalid_page_status_rejected():
    with pytest.raises(ValueError):
        certify_completeness(
            (page(1, status_code=700),),
            mode=PaginationMode.PAGE_NUMBER,
            termination_reason="explicit_end",
        )
