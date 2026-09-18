"""Versioned evaluation-corpus contract for research-quality evidence.

This module describes corpus/case provenance and replay metadata. It does not own
promotion, truth, signing, or production authorization; those remain with the
evaluation/promotion authority in the protected runtime.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json


SCHEMA = "evaluation-corpus/v1"
MAX_CASES = 10_000


class ReplayMode(StrEnum):
    DETERMINISTIC = "deterministic"
    SNAPSHOT = "snapshot"
    LIVE_SOURCE = "live_source"


class ApprovalStatus(StrEnum):
    UNAPPROVED = "unapproved"
    APPROVED_OFFLINE = "approved_offline"
    APPROVED_REAL_SOURCE = "approved_real_source"


class LeakageClass(StrEnum):
    CLEAN = "clean"
    SUSPECTED = "suspected"
    UNTRUSTED_EVALUATION = "untrusted_evaluation"


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    corpus_id: str
    corpus_version: str
    category: str
    population: str
    source_family: str
    input_digest: str
    expected_invariants: tuple[str, ...]
    oracle_ref: str | None = None
    snapshot_ref: str | None = None
    replay_mode: ReplayMode = ReplayMode.DETERMINISTIC
    leakage_class: LeakageClass = LeakageClass.CLEAN

    def validate(self) -> None:
        for name, value in (
            ("case_id", self.case_id),
            ("corpus_id", self.corpus_id),
            ("corpus_version", self.corpus_version),
            ("category", self.category),
            ("population", self.population),
            ("source_family", self.source_family),
            ("input_digest", self.input_digest),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
        if len(self.input_digest) != 64 or any(char not in "0123456789abcdef" for char in self.input_digest.lower()):
            raise ValueError("input_digest must be a SHA-256 hex digest")
        if not self.expected_invariants or any(not item.strip() for item in self.expected_invariants):
            raise ValueError("expected_invariants must contain non-empty values")
        if self.replay_mode is ReplayMode.SNAPSHOT and not (self.snapshot_ref or "").strip():
            raise ValueError("snapshot replay requires snapshot_ref")
        if self.replay_mode is ReplayMode.LIVE_SOURCE and not (self.oracle_ref or "").strip():
            raise ValueError("live-source replay requires oracle_ref")
        if self.leakage_class is LeakageClass.CLEAN and (
            "leakage" in self.category.casefold()
            or "contaminat" in self.category.casefold()
        ):
            raise ValueError("clean case cannot be labelled as a leakage/contamination category")

    def digest(self) -> str:
        self.validate()
        payload = {
            "schema": SCHEMA,
            "case_id": self.case_id,
            "corpus_id": self.corpus_id,
            "corpus_version": self.corpus_version,
            "category": self.category,
            "population": self.population,
            "source_family": self.source_family,
            "input_digest": self.input_digest,
            "expected_invariants": list(self.expected_invariants),
            "oracle_ref": self.oracle_ref,
            "snapshot_ref": self.snapshot_ref,
            "replay_mode": self.replay_mode.value,
            "leakage_class": self.leakage_class.value,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True)
class EvaluationCorpusManifest:
    corpus_id: str
    corpus_version: str
    owner: str
    approval_status: ApprovalStatus
    cases: tuple[EvaluationCase, ...]
    oracle_registry_version: str
    provenance_revision: str
    approval_receipt_ref: str | None = None

    def validate(self) -> None:
        for name, value in (
            ("corpus_id", self.corpus_id),
            ("corpus_version", self.corpus_version),
            ("owner", self.owner),
            ("oracle_registry_version", self.oracle_registry_version),
            ("provenance_revision", self.provenance_revision),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
        if not self.cases:
            raise ValueError("evaluation corpus must contain at least one case")
        if len(self.cases) > MAX_CASES:
            raise ValueError("evaluation corpus exceeds case limit")
        ids = {case.case_id for case in self.cases}
        if len(ids) != len(self.cases):
            raise ValueError("evaluation corpus contains duplicate case IDs")
        for case in self.cases:
            case.validate()
            if case.corpus_id != self.corpus_id or case.corpus_version != self.corpus_version:
                raise ValueError("evaluation case corpus identity does not match manifest")
        if self.approval_status is not ApprovalStatus.UNAPPROVED and not (self.approval_receipt_ref or "").strip():
            raise ValueError("approved corpus requires approval_receipt_ref")

    def digest(self) -> str:
        self.validate()
        payload = {
            "schema": SCHEMA,
            "corpus_id": self.corpus_id,
            "corpus_version": self.corpus_version,
            "owner": self.owner,
            "approval_status": self.approval_status.value,
            "cases": [case.digest() for case in sorted(self.cases, key=lambda item: item.case_id)],
            "oracle_registry_version": self.oracle_registry_version,
            "provenance_revision": self.provenance_revision,
            "approval_receipt_ref": self.approval_receipt_ref,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


def detect_corpus_collisions(
    manifest: EvaluationCorpusManifest,
    *,
    known_input_digests: tuple[str, ...] = (),
    known_oracle_refs: tuple[str, ...] = (),
) -> tuple[str, ...]:
    manifest.validate()
    findings: list[str] = []
    seen_inputs: set[str] = set(known_input_digests)
    seen_oracles: set[str] = set(known_oracle_refs)
    for case in manifest.cases:
        if case.input_digest in seen_inputs:
            findings.append(f"input_digest_collision:{case.case_id}")
        seen_inputs.add(case.input_digest)
        if case.oracle_ref and case.oracle_ref in seen_oracles:
            findings.append(f"oracle_ref_collision:{case.case_id}")
        if case.oracle_ref:
            seen_oracles.add(case.oracle_ref)
        if case.leakage_class is not LeakageClass.CLEAN:
            findings.append(f"declared_leakage:{case.case_id}:{case.leakage_class.value}")
    return tuple(sorted(findings))


def replay_manifest_digest(manifest: EvaluationCorpusManifest) -> str:
    """Stable replay identity; execution remains owned by the benchmark/runtime owner."""
    return manifest.digest()
