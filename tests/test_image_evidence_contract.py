import pytest

from backend.image_evidence.contract import (
    IMAGE_EVIDENCE_CONTRACT_VERSION,
    ImageEvidenceMode,
    ImageEvidenceRequest,
    ImageEvidenceResult,
    ImageEvidenceStatus,
    ImageObservation,
    ImageRegion,
    image_content_fingerprint,
    select_image_modes,
)


def fingerprint():
    return image_content_fingerprint(b"image")


def test_image_evidence_preserves_source_fingerprint_and_regions():
    region = ImageRegion("r1", 1, 2, 30, 40)
    obs = ImageObservation(
        "obs-1",
        ImageEvidenceMode.OCR,
        ImageEvidenceStatus.OBSERVED,
        "16 GB",
        980,
        region,
        fingerprint(),
        model_version="ocr-v1",
    )
    result = ImageEvidenceResult(IMAGE_EVIDENCE_CONTRACT_VERSION, fingerprint(), (obs,))
    result.validate()
    assert obs.region == region
    assert result.derived is True


def test_unreadable_and_unknown_observations_do_not_claim_values():
    for status in (ImageEvidenceStatus.UNKNOWN, ImageEvidenceStatus.UNREADABLE, ImageEvidenceStatus.BLOCKED):
        obs = ImageObservation("obs", ImageEvidenceMode.OCR, status, None, None, None, fingerprint())
        obs.validate()


def test_image_contract_validation_is_fail_closed():
    with pytest.raises(ValueError):
        ImageRegion("", 0, 0, 1, 1).validate()
    with pytest.raises(ValueError):
        ImageRegion("r", 0, 0, 0, 1).validate()
    with pytest.raises(ValueError):
        ImageRegion("r", -1, 0, 1, 1).validate()
    with pytest.raises(ValueError):
        ImageObservation("o", ImageEvidenceMode.OCR, ImageEvidenceStatus.OBSERVED, None, 900, None, fingerprint()).validate()
    with pytest.raises(ValueError):
        ImageObservation("o", ImageEvidenceMode.OCR, ImageEvidenceStatus.OBSERVED, "x", 1001, None, fingerprint()).validate()
    with pytest.raises(ValueError):
        ImageObservation("o", ImageEvidenceMode.OCR, ImageEvidenceStatus.OBSERVED, "x", 900, None, "bad").validate()
    with pytest.raises(ValueError):
        ImageObservation("o", ImageEvidenceMode.OCR, ImageEvidenceStatus.UNKNOWN, "x", None, None, fingerprint()).validate()


def test_image_result_rejects_mismatched_or_authoritative_outputs():
    obs = ImageObservation("o", ImageEvidenceMode.OCR, ImageEvidenceStatus.OBSERVED, "x", 500, None, "a" * 64)
    with pytest.raises(ValueError):
        ImageEvidenceResult("v0", "a" * 64, ()).validate()
    with pytest.raises(ValueError):
        ImageEvidenceResult(IMAGE_EVIDENCE_CONTRACT_VERSION, "a" * 64, (obs,), derived=False).validate()
    with pytest.raises(ValueError):
        ImageEvidenceResult(IMAGE_EVIDENCE_CONTRACT_VERSION, "b" * 64, (obs,)).validate()


def test_selective_routing_is_deterministic_and_budget_bounded():
    request = ImageEvidenceRequest(
        fingerprint(),
        allowed_modes=(ImageEvidenceMode.OCR, ImageEvidenceMode.PERCEPTUAL_FINGERPRINT),
        max_observations=4,
    )
    assert select_image_modes(request, budget_units=1) == (ImageEvidenceMode.OCR,)
    assert select_image_modes(request, budget_units=10) == (
        ImageEvidenceMode.OCR,
        ImageEvidenceMode.PERCEPTUAL_FINGERPRINT,
    )
    assert select_image_modes(request, budget_units=0) == ()
    with pytest.raises(ValueError):
        ImageEvidenceRequest("bad").validate()
