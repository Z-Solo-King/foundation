from __future__ import annotations

from collections import Counter
from pathlib import Path
import argparse
import json

from benchmark.reproducibility import ensure_compatible

SCHEMA = "project-improvement-baseline/v1"


def _count_status(payload: dict[str, object], status: str) -> int:
    counts = payload.get("status_counts", {})
    return int(counts.get(status, 0)) if isinstance(counts, dict) else 0


def _useful_findings(payload: dict[str, object]) -> int:
    total = 0
    programs = payload.get("programs", [])
    if not isinstance(programs, list):
        return 0
    for program in programs:
        if not isinstance(program, dict):
            continue
        measurement = program.get("measurement", {})
        if isinstance(measurement, dict):
            total += int(measurement.get("useful_findings", 0) or 0)
    return total


def _high_signal_count(payload: dict[str, object]) -> int:
    signals = payload.get("improvement_signals", [])
    if not isinstance(signals, list):
        return 0
    return sum(1 for signal in signals if isinstance(signal, dict) and signal.get("severity") == "high")


def _signal_types(payload: dict[str, object]) -> Counter[str]:
    signals = payload.get("improvement_signals", [])
    if not isinstance(signals, list):
        return Counter()
    return Counter(str(signal.get("type")) for signal in signals if isinstance(signal, dict) and signal.get("type"))


def _no_baseline(current: dict[str, object], reason: str, **extra: object) -> dict[str, object]:
    result = {
        "schema": SCHEMA,
        "available": False,
        "decision": "NO_BASELINE",
        "reason": reason,
        "current_research_id": current.get("research_id"),
        "current_revision": (current.get("project_snapshot") or {}).get("revision"),
    }
    result.update(extra)
    return result


def compare(current: dict[str, object], previous: dict[str, object] | None) -> dict[str, object]:
    if previous is None:
        return _no_baseline(current, "no prior completed nightly project-improvement summary was available")
    try:
        compatible, compatibility_errors = ensure_compatible(
            current.get("reproducibility"),
            previous.get("reproducibility"),
        )
    except ValueError as exc:
        return _no_baseline(current, "missing or invalid reproducibility metadata", compatibility_errors=[str(exc)])
    if not compatible:
        return _no_baseline(current, "current and previous artifacts are not reproducibly comparable", compatibility_errors=compatibility_errors)

    current_completed = _count_status(current, "completed")
    previous_completed = _count_status(previous, "completed")
    current_useful = _useful_findings(current)
    previous_useful = _useful_findings(previous)
    current_high = _high_signal_count(current)
    previous_high = _high_signal_count(previous)
    current_execution = str(current.get("execution_state", ""))
    previous_execution = str(previous.get("execution_state", ""))
    current_types = _signal_types(current)
    previous_types = _signal_types(previous)
    regressed = ((current_execution != "completed" and previous_execution == "completed") or current_completed < previous_completed or current_useful < previous_useful or current_high > previous_high)
    improved = ((current_execution == "completed" and previous_execution != "completed") or current_completed > previous_completed or current_useful > previous_useful or current_high < previous_high)
    if regressed:
        decision = "REGRESSED"
    elif improved:
        decision = "IMPROVED"
    else:
        decision = "STABLE"
    return {
        "schema": SCHEMA,
        "available": True,
        "decision": decision,
        "current_research_id": current.get("research_id"),
        "previous_research_id": previous.get("research_id"),
        "current_revision": (current.get("project_snapshot") or {}).get("revision"),
        "previous_revision": (previous.get("project_snapshot") or {}).get("revision"),
        "reproducibility": {
            "suite": (current.get("reproducibility") or {}).get("suite"),
            "suite_version": (current.get("reproducibility") or {}).get("suite_version"),
            "evidence_tier": (current.get("reproducibility") or {}).get("evidence_tier"),
            "corpus_id": (current.get("reproducibility") or {}).get("corpus_id"),
            "corpus_version": (current.get("reproducibility") or {}).get("corpus_version"),
            "configuration_digest": (current.get("reproducibility") or {}).get("configuration_digest"),
        },
        "metrics": {
            "completed_programs_delta": current_completed - previous_completed,
            "useful_findings_delta": current_useful - previous_useful,
            "high_severity_signals_delta": current_high - previous_high,
            "program_count_delta": int(current.get("program_count", 0) or 0) - int(previous.get("program_count", 0) or 0),
        },
        "signal_type_changes": {
            "added": sorted(set(current_types) - set(previous_types)),
            "resolved": sorted(set(previous_types) - set(current_types)),
        },
        "rules": {
            "regression": "execution degradation, fewer completed programs, fewer useful findings, or more high-severity improvement signals",
            "improvement": "recovery to completed execution, more completed programs, more useful findings, or fewer high-severity improvement signals",
            "tie_break": "REGRESSED takes precedence over IMPROVED when both conditions are true",
            "compatibility": "baseline comparison requires matching repository, suite/version, configuration, corpus and evidence tier; the previous baseline must be completed, while a partial current run may be classified as REGRESSED",
        },
    }


def load_summary(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "project-improvement-research/v1":
        raise ValueError("unsupported project-improvement summary schema")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare the current nightly project research against the prior baseline")
    parser.add_argument("--current", required=True)
    parser.add_argument("--previous", required=False, default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    current = load_summary(Path(args.current))
    previous = load_summary(Path(args.previous)) if args.previous and Path(args.previous).exists() else None
    result = compare(current, previous)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"event": "project_research_baseline", "schema": SCHEMA, "decision": result["decision"], "available": result["available"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
