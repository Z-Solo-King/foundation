# Evidence certificate authority

`backend/evidence_certificate.py` is the canonical `EvidenceCertificate` implementation.

`backend/intelligence/certificates.py` is a compatibility facade for the historical import path. It intentionally preserves the historical boolean-return behavior of `verify_certificate()` for invalid spans while delegating certificate construction and verification to the canonical implementation.

Do not add a second certificate schema; extend the canonical type or add an explicit compatibility adapter when legacy callers require a different constructor shape.
