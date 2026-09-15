"""Validate the repository's human-readable ownership and navigation map."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_PRIVATE_REPO = "Z-Solo-King/operations"
EXTERNAL_PREFIXES = (f"{_PRIVATE_REPO}:", "http://", "https://")
MAP_FILE = "REPOSITORY_MAP.json"


def _is_external_reference(value: str) -> bool:
    return value.startswith(EXTERNAL_PREFIXES)


def _looks_like_repo_path(value: str) -> bool:
    return not _is_external_reference(value) and not value.startswith("/") and ("/" in value or "." in value)


def _iter_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_strings(item)


def _check_path(root: Path, value: str, errors: list[str], source: str) -> None:
    if not _looks_like_repo_path(value):
        return
    candidate = value[:-1] if value.endswith("/") else value
    if not (root / candidate).exists():
        errors.append(f"{source}: repository path does not exist: {value}")


def validate_repository(root: Path) -> list[str]:
    """Return a list of repository-map errors for *root*."""
    errors: list[str] = []
    map_path = root / MAP_FILE

    if not map_path.exists():
        return [f"missing repository map: {MAP_FILE}"]

    try:
        mapping = json.loads(map_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{MAP_FILE}: invalid JSON: {exc}"]

    for value in _iter_strings(mapping.get("read_first", [])):
        _check_path(root, value, errors, "REPOSITORY_MAP.read_first")
    for value in _iter_strings(mapping.get("canonical", {})):
        _check_path(root, value, errors, "REPOSITORY_MAP.canonical")
    for value in _iter_strings(mapping.get("maintenance", {})):
        _check_path(root, value, errors, "REPOSITORY_MAP.maintenance")

    for value in _iter_strings(mapping):
        if "private/" in value.lower() and _PRIVATE_REPO.lower() not in value.lower():
            errors.append(f"REPOSITORY_MAP: ambiguous private reference: {value}")

    if mapping.get("repository") != "Z-Solo-King/foundation":
        errors.append("REPOSITORY_MAP.repository must identify Z-Solo-King/foundation")

    if mapping.get("schema_version") != "repository-map/v1":
        errors.append("REPOSITORY_MAP.schema_version must be repository-map/v1")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_repository(root)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("repository map: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
