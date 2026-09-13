"""Deterministic evaluation receipts that bind results to their evaluation inputs.

The receipt is evidence about an evaluation run, not a promotion decision. A
protected policy layer may consume a verified receipt, but this public module
does not grant promotion authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from typing import Mapping


def _fingerprint(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class EvaluationReceipt:
    receipt_id: str
    candidate_fingerprint: str
    baseline_fingerprint: str
    corpus_fingerprint: str
    oracle_fingerprint: str
    suite_version: str
    benchmark_count: int
    metrics: tuple[tuple[str, float], ...]
    passed: bool
    created_at: str
    evaluator_version: str
    artifact_hash: str

    def validate(self) -> None:
        bounded = (
            ("receipt_id", self.receipt_id, 128),
            ("candidate_fingerprint", self.candidate_fingerprint, 128),
            ("baseline_fingerprint", self.baseline_fingerprint, 128),
            ("corpus_fingerprint", self.corpus_fingerprint, 128),
            ("oracle_fingerprint", self.oracle_fingerprint, 128),
            ("suite_version", self.suite_version, 96),
            ("created_at", self.created_at, 64),
            ("evaluator_version", self.evaluator_version, 96),
            ("artifact_hash", self.artifact_hash, 128),
        )
        for name, value, limit in bounded:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must not be empty")
            if len(value) > limit:
                raise ValueError(f"{name} exceeds bounded length")
        if self.benchmark_count <= 0:
            raise ValueError("benchmark_count must be positive")
        if not self.metrics:
            raise ValueError("metrics must not be empty")
        seen: set[str] = set()
        for name, value in self.metrics:
            if not isinstance(name, str) or not name.strip():
                raise ValueError("metric name must not be empty")
            if len(name) > 96:
                raise ValueError("metric name exceeds bounded length")
            if name in seen:
                raise ValueError(f"duplicate metric: {name}")
            seen.add(name)
            if not math.isfinite(value):
                raise ValueError(f"metric {name} must be finite")

    def fingerprint(self) -> str:
        self.validate()
        return _fingerprint(
            {
                "receipt_id": self.receipt_id,
                "candidate_fingerprint": self.candidate_fingerprint,
                "baseline_fingerprint": self.baseline_fingerprint,
                "corpus_fingerprint": self.corpus_fingerprint,
                "oracle_fingerprint": self.oracle_fingerprint,
                "suite_version": self.suite_version,
                "benchmark_count": self.benchmark_count,
                "metrics": self.metrics,
                "passed": self.passed,
                "created_at": self.created_at,
                "evaluator_version": self.evaluator_version,
                "artifact_hash": self.artifact_hash,
            }
        )

    def verify_binding(
        self,
        *,
        candidate_fingerprint: str,
        baseline_fingerprint: str,
        corpus_fingerprint: str,
        oracle_fingerprint: str,
        min_benchmark_count: int = 1,
    ) -> bool:
        """Verify that this receipt is bound to the expected evaluation inputs."""
        self.validate()
        return (
            self.candidate_fingerprint == candidate_fingerprint
            and self.baseline_fingerprint == baseline_fingerprint
            and self.corpus_fingerprint == corpus_fingerprint
            and self.oracle_fingerprint == oracle_fingerprint
            and self.benchmark_count >= min_benchmark_count
        )

    def metric_map(self) -> Mapping[str, float]:
        self.validate()
        return dict(self.metrics)
