from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from typing import Any

SCHEMA = "nightly-research-program/v1"
_ALLOWED_TOP_LEVEL = frozenset({"schema", "program_id", "lane", "slot", "status", "measurement", "findings"})
_ALLOWED_MEASUREMENT = frozenset({
    "allocated_agents",
    "completed_agents",
    "failed_agents",
    "wall_clock_seconds",
    "agent_seconds",
    "useful_findings",
    "unique_sources",
    "duplicate_rate",
    "answer_quality_0_to_10",
    "follow_up_questions",
})
_ALLOWED_FINDING = frozenset({
    "claim",
    "source_url",
    "source_family",
    "acquisition_method",
    "evidence_status",
})
_ALLOWED_STATUS = frozenset({"completed", "partial", "blocked", "failed"})
_SECRET_PATTERN = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|private[_-]?key|password|authorization)\s*[:=]\s*\S+"
)
_PRIVATE_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "host.docker.internal"})


def _safe_text(value: object, *, field: str, required: bool = False) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    text = value.strip()
    if required and not text:
        raise ValueError(f"{field} must be non-empty")
    if len(text) > 12_000:
        raise ValueError(f"{field} exceeds 12000 characters")
    if _SECRET_PATTERN.search(text) or "-----BEGIN " in text.upper() and "PRIVATE KEY-----" in text.upper():
        raise ValueError(f"{field} contains credential material")
    return text


def _safe_public_url(value: object) -> str | None:
    text = _safe_text(value, field="source_url")
    if text is None:
        return None
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("source_url must be an absolute HTTP(S) URL")
    if parsed.hostname.lower() in _PRIVATE_HOSTS:
        raise ValueError("source_url points to a private/local host")
    return text


def validate_record(record: object, *, expected_lane: int | None = None) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("artifact record must be an object")
    unknown = set(record) - _ALLOWED_TOP_LEVEL
    if unknown:
        raise ValueError(f"artifact record contains non-public fields: {sorted(unknown)}")
    if record.get("schema") != SCHEMA:
        raise ValueError(f"unsupported public research schema: {record.get('schema')!r}")

    program_id = _safe_text(record.get("program_id"), field="program_id", required=True)
    lane = record.get("lane")
    slot = record.get("slot")
    if not isinstance(lane, int) or lane not in {0, 1, 2}:
        raise ValueError("lane must be 0, 1 or 2")
    if expected_lane is not None and lane != expected_lane:
        raise ValueError(f"lane mismatch: expected {expected_lane}, got {lane}")
    if not isinstance(slot, int) or not 0 <= slot < 8:
        raise ValueError("slot must be between 0 and 7")
    status = record.get("status")
    if status not in _ALLOWED_STATUS:
        raise ValueError(f"unsupported program status: {status!r}")

    measurement = record.get("measurement")
    if not isinstance(measurement, dict):
        raise ValueError("measurement must be an object")
    unknown_measurement = set(measurement) - _ALLOWED_MEASUREMENT
    if unknown_measurement:
        raise ValueError(f"measurement contains non-public fields: {sorted(unknown_measurement)}")
    for key, value in measurement.items():
        if key == "answer_quality_0_to_10" and value is None:
            continue
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"measurement.{key} must be numeric or null")

    findings = record.get("findings")
    if not isinstance(findings, list):
        raise ValueError("findings must be a list")
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError("each finding must be an object")
        unknown_finding = set(finding) - _ALLOWED_FINDING
        if unknown_finding:
            raise ValueError(f"finding contains non-public fields: {sorted(unknown_finding)}")
        _safe_text(finding.get("claim"), field="finding.claim", required=True)
        _safe_public_url(finding.get("source_url"))
        for field in ("source_family", "acquisition_method", "evidence_status"):
            _safe_text(finding.get(field), field=f"finding.{field}")

    return {
        "program_id": program_id,
        "lane": lane,
        "slot": slot,
        "status": status,
        "finding_count": len(findings),
    }


def validate_jsonl(path: Path, *, expected_lane: int | None = None) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"missing research artifact: {path}")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    errors: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            summary = validate_record(record, expected_lane=expected_lane)
            if summary["program_id"] in seen:
                raise ValueError(f"duplicate program_id: {summary['program_id']}")
            seen.add(summary["program_id"])
            rows.append(summary)
        except (json.JSONDecodeError, ValueError) as exc:
            errors.append(f"line {line_number}: {exc}")
    if errors:
        raise ValueError("public research artifact boundary failed: " + " | ".join(errors))
    return {"schema": "public-research-artifact-validation/v1", "records": len(rows), "program_ids": sorted(seen)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a nightly research artifact before public upload.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--lane", type=int, choices=(0, 1, 2))
    args = parser.parse_args()
    report = validate_jsonl(args.path, expected_lane=args.lane)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
