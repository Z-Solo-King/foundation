from tools.check_context_budget import PROD_BYTES, TEST_BYTES


def test_budget_constants_are_bounded():
    assert PROD_BYTES <= 30_000
    assert TEST_BYTES <= 45_000
