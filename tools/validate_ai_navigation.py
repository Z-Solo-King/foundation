"""Deterministically validate AI-facing repository navigation metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_PRIVATE_REPO = "/".join(("Z-Solo-King", "operations"))
EXTERNAL_PREFIXES = (f"{_PRIVATE_REPO}:", "http://", "https://")


def _is_external_reference(value: str) -> bool:
    return value.startswith(EXTERNAL_PREFIXES)


def _looks_like_repo_path(value: str) -> bool:
    return (
        not _is_external_reference(value)
        and not value.startswith("/")
        and ("/" in value or "." in value)
    )


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
    errors: list[str] = []
    navigation_path = root / "AI_NAVIGATION_INDEX.json"

    if not navigation_path.exists():
        return ["missing navigation metadata: AI_NAVIGATION_INDEX.json"]

    try:
        navigation = json.loads(navigation_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"AI_NAVIGATION_INDEX.json: invalid JSON: {exc}"]

    for value in _iter_strings(navigation.get("read_first", [])):
        _check_path(root, value, errors, "AI_NAVIGATION_INDEX.read_first")

    for value in _iter_strings(navigation.get("canonical", {})):
        _check_path(root, value, errors, "AI_NAVIGATION_INDEX.canonical")

    for value in _iter_strings(navigation.get("maintenance", {})):
        _check_path(root, value, errors, "AI_NAVIGATION_INDEX.maintenance")

    for value in _iter_strings(navigation):
        lowered = value.lower()
        if "private/" in lowered and _PRIVATE_REPO.lower() not in lowered:
            errors.append(f"AI_NAVIGATION_INDEX: ambiguous private reference: {value}")

    if navigation.get("repo") != "Z-Solo-King/foundation":
        errors.append("AI_NAVIGATION_INDEX.repo must identify Z-Solo-King/foundation")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_repository(root)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("AI navigation metadata: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
