# Feature Governance CI Integration

The family governance workflow validates two levels:

1. Extractor capability coverage: capability -> owner -> entrypoint -> policy -> evidence -> work item -> migration disposition.
2. Whole-feature coverage: feature domain -> source/function -> policy -> dedicated test surface -> evidence -> active work item -> migration disposition.

Foundation owns the workflow. Operations owns the private runtime and governance definitions. The workflow reads the Operations tree through the existing read-only GitHub App boundary and stores reports as evidence artifacts.

The audit is intentionally non-authoritative for runtime promotion. A passing structural audit does not close #157, #1247/#1249, #597 or #603 and does not replace production or Cloudflare runtime receipts.
