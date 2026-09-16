"""Public deterministic utilities for observed data and bounded execution."""

from .field_routing import FIELD_ALIASES, FIELD_FAMILIES, RoutedField, route_field, route_fields
from .normalization import normalize_specs, normalize_stock
from .outcome import RETRYABLE_OUTCOMES, TERMINAL_OUTCOMES, StageOutcome, is_retryable, is_terminal, validate_outcome
from .product_identity import IdentityDecision, identity_matches
from .product_mapping import map_product
from .quality import PlausibilitySignal, evaluate_price_spec_plausibility
from .stage_receipt import StageReceipt, can_resume, fingerprint, validate_chain
from .token_efficiency import EfficiencyGate, TokenEfficiencyObservation, compare_efficiency

__all__ = [
    "FIELD_ALIASES",
    "FIELD_FAMILIES",
    "PlausibilitySignal",
    "RoutedField",
    "StageReceipt",
    "StageOutcome",
    "TokenEfficiencyObservation",
    "EfficiencyGate",
    "IdentityDecision",
    "RETRYABLE_OUTCOMES",
    "TERMINAL_OUTCOMES",
    "can_resume",
    "compare_efficiency",
    "evaluate_price_spec_plausibility",
    "fingerprint",
    "identity_matches",
    "is_retryable",
    "is_terminal",
    "map_product",
    "normalize_specs",
    "normalize_stock",
    "route_field",
    "route_fields",
    "validate_chain",
    "validate_outcome",
]
