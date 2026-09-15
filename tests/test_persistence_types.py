from backend.persistence.d1 import EvidenceLinkageRecord, EvidenceRecord


def test_persisted_evidence_linkage_has_explicit_type_name():
    assert EvidenceRecord is EvidenceLinkageRecord
