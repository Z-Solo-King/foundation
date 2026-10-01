#!/usr/bin/env python3
"""Delete stale Backblaze B2 repository-backup object versions after verification."""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

PREFIX = "repository-backup/"
DELETE_BATCH_SIZE = 1000


def _aws_json(*args: str) -> dict:
    result = subprocess.run(
        ["aws", "s3api", *args, "--output", "json"],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout or "{}")


def load_keep_keys(keep_file: Path) -> set[str]:
    keys: set[str] = set()
    for line in keep_file.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        fields = line.split("\t")
        if not fields or not fields[0].startswith(PREFIX):
            raise SystemExit("backup keep-file contains a key outside the repository-backup/ prefix")
        keys.add(fields[0])
    if not keys:
        raise SystemExit("backup keep-file is empty")
    return keys


def deletion_plan(payload: dict, keep_keys: set[str]) -> list[dict[str, str]]:
    deletions: list[dict[str, str]] = []
    for field in ("Versions", "DeleteMarkers"):
        for row in payload.get(field, []) or []:
            key = str(row.get("Key") or "")
            version_id = str(row.get("VersionId") or "")
            if not key.startswith(PREFIX) or not version_id:
                continue
            if key in keep_keys and row.get("IsLatest") is True:
                continue
            deletions.append({"Key": key, "VersionId": version_id})
    return deletions


def delete_versions(bucket: str, endpoint: str, deletions: list[dict[str, str]]) -> None:
    for start in range(0, len(deletions), DELETE_BATCH_SIZE):
        batch = deletions[start : start + DELETE_BATCH_SIZE]
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".json") as handle:
            json.dump({"Objects": batch, "Quiet": True}, handle)
            path = handle.name
        try:
            _aws_json(
                "delete-objects",
                "--bucket", bucket,
                "--endpoint-url", endpoint,
                "--delete", f"file://{path}",
            )
        finally:
            Path(path).unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--endpoint", required=True)
    parser.add_argument("--keep-file", required=True)
    args = parser.parse_args()

    keep_keys = load_keep_keys(Path(args.keep_file))
    payload = _aws_json(
        "list-object-versions",
        "--bucket", args.bucket,
        "--prefix", PREFIX,
        "--endpoint-url", args.endpoint,
    )
    deletions = deletion_plan(payload, keep_keys)
    delete_versions(args.bucket, args.endpoint, deletions)
    print(
        f"B2 retention cleanup: kept_current_keys={len(keep_keys)} "
        f"deleted_versions={len(deletions)} prefix={PREFIX}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
