# Research safeguards 371–374

Issues 371–374 are implemented by the deterministic core changes in `foundation_core/stage_receipt.py` and `foundation_core/token_efficiency.py`, with adversarial regression coverage in `tests/test_research_safeguards_371_374.py`.

## 371 — receipt expiry
`StageReceipt` accepts optional timezone-aware `created_at` and `expires_at`; `can_resume()` rejects expired receipts while retaining backwards-compatible unlimited behavior when no expiry is supplied.

## 372 — chain resource budget
`validate_chain()` accepts optional `max_resource_units` and rejects chains whose cumulative `resource_units` exceed the supplied budget.

## 373 — output-token floor
`EfficiencyGate.min_output_tokens_ratio` can require a candidate to retain a configured fraction of baseline output tokens before efficiency acceptance.

## 374 — context amplification
`EfficiencyGate.max_context_amplification_ratio` can reject candidates that consume excessive total tokens per output token, including cache-hit scenarios that hide context growth.
