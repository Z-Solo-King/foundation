"""Bound decoded JSON structure before endpoint/model processing."""
from __future__ import annotations

MAX_JSON_DEPTH = 32
MAX_JSON_COLLECTION_ITEMS = 1_024


def validate_json_shape(value, *, max_depth=MAX_JSON_DEPTH, max_collection_items=MAX_JSON_COLLECTION_ITEMS):
    """Reject pathological decoded JSON without truncating accepted payloads."""
    if not isinstance(max_depth, int) or max_depth < 1:
        raise ValueError("max_depth must be a positive integer")
    if not isinstance(max_collection_items, int) or max_collection_items < 1:
        raise ValueError("max_collection_items must be a positive integer")

    stack = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        if depth > max_depth:
            raise ValueError("JSON nesting exceeds the supported depth")
        if isinstance(current, dict):
            if len(current) > max_collection_items:
                raise ValueError("JSON object exceeds the supported field count")
            stack.extend((item, depth + 1) for item in current.values())
        elif isinstance(current, list):
            if len(current) > max_collection_items:
                raise ValueError("JSON array exceeds the supported item count")
            stack.extend((item, depth + 1) for item in current)
