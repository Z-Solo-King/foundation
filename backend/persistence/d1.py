"""D1 persistence models and an in-memory test repository.

Production Cloudflare persistence keeps compact metadata, run state, evidence graph
relationships, indexes, and source lineage in D1. Large raw documents and artifacts
are stored through the provider-neutral artifact interface, currently backed by
Backblaze B2. Production idempotency/CAS behavior is implemented by the Cloudflare
adapter; this in-memory repository is only a deterministic test double.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RunRecord:
    """Persisted research run state in D1."""
    run_id: str
    question: str
    depth: str
    status: str
    created_at: datetime
    updated_at: datetime
    source_budget: int
    evidence_budget: int
    metadata_json: str


@dataclass(frozen=True)
class EvidenceRecord:
    """Persisted evidence span linkage in D1."""
    evidence_id: str
    run_id: str
    observation_id: str
    source_id: str
    claim_id: str | None
    span_start: int
    span_end: int
    content_hash: str
    created_at: datetime


@dataclass(frozen=True)
class SourceLineageRecord:
    """Persisted source lineage in D1."""
    source_id: str
    family_id: str
    parent_source_id: str | None
    lineage_type: str
    first_observed: datetime
    last_observed: datetime


@dataclass(frozen=True)
class DocumentVersionRecord:
    """Persisted document version snapshot in D1."""
    version_id: str
    observation_id: str
    source_id: str
    retrieved_at: datetime
    etag: str | None
    content_hash: str
    artifact_ref: str


class D1Repository:
    """Deterministic in-memory test double for D1 persistence."""

    def __init__(self):
        self._runs: dict[str, RunRecord] = {}
        self._evidence: dict[str, EvidenceRecord] = {}
        self._lineage: dict[str, SourceLineageRecord] = {}
        self._versions: dict[str, DocumentVersionRecord] = {}

    def create_run(self, record: RunRecord) -> RunRecord:
        """Insert a run record without silently overwriting an existing run."""
        if record.run_id in self._runs:
            raise ValueError(f"run {record.run_id} already exists")
        self._runs[record.run_id] = record
        return record

    def update_run(self, record: RunRecord) -> RunRecord:
        """Update a run record if it exists."""
        if record.run_id not in self._runs:
            raise ValueError(f"run {record.run_id} not found")
        self._runs[record.run_id] = record
        return record

    def get_run(self, run_id: str) -> RunRecord | None:
        """Retrieve a run record by ID."""
        return self._runs.get(run_id)

    def add_evidence(self, record: EvidenceRecord) -> EvidenceRecord:
        """Insert evidence linkage."""
        if record.evidence_id in self._evidence:
            raise ValueError(f"evidence {record.evidence_id} already exists")
        self._evidence[record.evidence_id] = record
        return record

    def evidence_for_run(self, run_id: str) -> list[EvidenceRecord]:
        """Retrieve all evidence for a run."""
        return [e for e in self._evidence.values() if e.run_id == run_id]

    def evidence_for_claim(self, claim_id: str) -> list[EvidenceRecord]:
        """Retrieve all evidence supporting a claim."""
        return [e for e in self._evidence.values() if e.claim_id == claim_id]

    def upsert_lineage(self, record: SourceLineageRecord) -> SourceLineageRecord:
        """Insert or update source lineage."""
        self._lineage[record.source_id] = record
        return record

    def get_lineage(self, source_id: str) -> SourceLineageRecord | None:
        """Retrieve lineage for a source."""
        return self._lineage.get(source_id)

    def lineage_for_family(self, family_id: str) -> list[SourceLineageRecord]:
        """Retrieve all sources in a family."""
        return [l for l in self._lineage.values() if l.family_id == family_id]

    def add_version(self, record: DocumentVersionRecord) -> DocumentVersionRecord:
        """Insert a document version record."""
        if record.version_id in self._versions:
            raise ValueError(f"version {record.version_id} already exists")
        self._versions[record.version_id] = record
        return record

    def versions_for_observation(self, observation_id: str) -> list[DocumentVersionRecord]:
        """Retrieve all versions of an observation."""
        return [v for v in self._versions.values() if v.observation_id == observation_id]
