"""Versioned real-source/oracle evaluation corpus contracts.

Measurement manifests are data contracts only; the existing evaluation authority
remains responsible for pass/fail and promotion decisions.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable

CORPUS_SCHEMA = "research-evaluation-corpus/v1"


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    case_class: str
    population: str
    expected_invariants: tuple[str, ...]
    oracle_provenance: str
    replay_mode: str = "deterministic"
    snapshot_id: str | None = None

    def validate(self) -> None:
        for name, value in (
            ("case_id", self.case_id),
            ("case_class", self.case_class),
            ("population", self.population),
            ("oracle_provenance", self.oracle_provenance),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if not self.expected_invariants or any(not item.strip() for item in self.expected_invariants):
            raise ValueError("expected_invariants must be non-empty")
        if self.replay_mode not in {"deterministic", "snapshot", "live"}:
            raise ValueError("replay_mode is invalid")
        if self.replay_mode == "snapshot" and not (self.snapshot_id or "").strip():
            raise ValueError("snapshot replay requires snapshot_id")

    @property
    def fingerprint(self) -> str:
        self.validate()
        payload = {
            "case_id": self.case_id,
            "case_class": self.case_class,
            "population": self.population,
            "expected_invariants": list(self.expected_invariants),
            "oracle_provenance": self.oracle_provenance,
            "replay_mode": self.replay_mode,
            "snapshot_id": self.snapshot_id,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CorpusManifest:
    version: str
    cases: tuple[EvaluationCase, ...]
    source: str = "repository"
    leakage_check_version: str = "leakage/v1"

    def validate(self) -> None:
        if self.version != CORPUS_SCHEMA:
            raise ValueError("unsupported corpus schema")
        if not self.cases:
            raise ValueError("corpus must contain at least one case")
        seen_ids: set[str] = set()
        seen_fingerprints: set[str] = set()
        for case in self.cases:
            case.validate()
            if case.case_id in seen_ids:
                raise ValueError("duplicate case_id")
            if case.fingerprint in seen_fingerprints:
                raise ValueError("duplicate case fingerprint")
            seen_ids.add(case.case_id)
            seen_fingerprints.add(case.fingerprint)
        if not self.leakage_check_version.strip():
            raise ValueError("leakage_check_version is required")

    @property
    def fingerprint(self) -> str:
        self.validate()
        payload = {
            "version": self.version,
            "source": self.source,
            "leakage_check_version": self.leakage_check_version,
            "cases": [
                {"case_id": c.case_id, "fingerprint": c.fingerprint}
                for c in sorted(self.cases, key=lambda item: item.case_id)
            ],
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def build_corpus_manifest(cases: Iterable[EvaluationCase], *, source: str = "repository") -> CorpusManifest:
    manifest = CorpusManifest(CORPUS_SCHEMA, tuple(cases), source=source)
    manifest.validate()
    return manifest
