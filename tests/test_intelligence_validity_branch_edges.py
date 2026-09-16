from datetime import datetime


def test_validity_overlap_rejects_right_end_before_left_start():
    from backend.intelligence.contradiction import TypedClaim, detect_typed_contradiction

    left = TypedClaim(
        "left", "E", "P", 1, "numeric",
        valid_from=datetime(2024, 2, 1), unit="kg",
    )
    right = TypedClaim(
        "right", "E", "P", 2, "numeric",
        valid_until=datetime(2024, 1, 1), unit="kg",
    )
    assert detect_typed_contradiction(left, right) is None
