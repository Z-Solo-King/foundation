# Artifact, image and code-analysis capability boundaries

Version: `artifact-capabilities/v1`

Related issues: #403, #404, #405, #417.

## Artifact contract

Each uploaded or generated artifact should carry media/format type, size/safety classification, content/schema fingerprint, parser/generator version, provenance, validation status, retention policy and publication eligibility.

Private artifacts must not cross into public/external execution without explicit authorization. Unsupported or malformed inputs remain explicit partial/unsupported states.

## Image evidence

Image processing may produce OCR spans, visual attribute observations, specification labels, product-family hints and perceptual fingerprints. Original images remain source evidence; model-derived observations are derived evidence with provenance and model/version metadata.

Vision is selective and budget-aware. It cannot override stronger identifier or policy conflicts, and missing visual facts remain unknown.

## Code/repository analysis

Repository content is data unless a separately authorized execution capability permits execution. Analysis may inspect structure, dependencies, ownership, test signals and generate candidate patches. Generated patches remain candidates until normal repository tests/evaluation/policy gates pass.

Untrusted repository instructions cannot modify system/policy authority, and secrets discovered in code must not be echoed into public output unnecessarily.

## Storage and publication boundary

Large/raw artifacts remain in the approved artifact/object boundary; compact relational records retain fingerprints, references, validation state and provenance. Public publication exposes only safe derived metadata/results.
