# Open-issue polyglot scanner synchronization

The canonical Foundation open-issue deep-scan workflow checks out Z-Solo-King/operations at main.

The Operations scanner implementation and its authoritative surface/rule contract therefore remain the source exercised by the Foundation deep-scan jobs. A scanner change must be merged to Operations main before the Foundation workflow can consume it.

The scan is an evidence-coverage gate only. REVIEW or missing runtime receipts remain acceptance blockers; a successful structural scan must not be interpreted as production/runtime certification.

- 2026-09-27: scanner JSON proxy merged on Operations main to normalize active cases across all four audit lanes.
