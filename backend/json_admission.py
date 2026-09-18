"""Bound decoded JSON structure before endpoint/model processing."""
from __future__ import annotations

import json

MAX_JSON_DEPTH = 32
MAX_JSON_COLLECTION_ITEMS = 1_024
MAX_JSON_STRING_CHARS = 131_072


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON object contains duplicate fields")
        result[key] = value
    return result


def parse_bounded_json(text: str):
    return json.loads(text, object_pairs_hook=_reject_duplicate_keys)


def validate_json_shape(
    value,
    *,
    max_depth=MAX_JSON_DEPTH,
    max_collection_items=MAX_JSON_COLLECTION_ITEMS,
    max_string_chars=MAX_JSON_STRING_CHARS,
):
    """Reject pathological decoded JSON without truncating accepted payloads."""
    if not isinstance(max_depth, int) or max_depth < 1:
        raise ValueError("max_depth must be a positive integer")
    if not isinstance(max_collection_items, int) or max_collection_items < 1:
        raise ValueError("max_collection_items must be a positive integer")
    if not isinstance(max_string_chars, int) or max_string_chars < 1:
        raise ValueError("max_string_chars must be a positive integer")

    stack = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        if depth > max_depth:
            raise ValueError("JSON nesting exceeds the supported depth")
        if isinstance(current, str):
            if len(current) > max_string_chars:
                raise ValueError("JSON string exceeds the supported length")
        elif isinstance(current, dict):
            if len(current) > max_collection_items:
                raise ValueError("JSON object exceeds the supported field count")
            stack.extend((item, depth + 1) for item in current.values())
        elif isinstance(current, list):
            if len(current) > max_collection_items:
                raise ValueError("JSON array exceeds the supported item count")
            stack.extend((item, depth + 1) for item in current)
