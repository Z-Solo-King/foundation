## 2026-09-23 CURRENT AUTHORITY RECONCILIATION

**Live main heads verified:**
- Foundation main: `121ff5017c6b11ebc103dbbd26bdffe639fcc8cb`
- Operations main: `b47aa056f50d27df9b5f552495a6cd862ae8a697`

**Runtime/deployment provenance actually observed:**
- Public Worker: `c465ed8cff860cf0f1a1d6de6655aaf9594f02d2`
- Private production Worker: `bfcfaf5941824559cc253ecb2fd7d517cb1f1d7f`
- Nightly research pin: `3a7e350ddd5648caf93f58651323425186544f66`

**Current queue:** Foundation #58/#157; Operations #145/#197/#340/#352/#385/#597/#603/#699/#711.
- No open implementation PRs.
- No open documentation PRs after the completed synchronization merges.

**Current evidence:**
- Latest completed nightly research #861 is blocked before provider execution; the newer scheduled run #862 is in progress.
- Latest completed extractor benchmark #330 failed its gate and used stale Operations #830 (`246e563...`); corrected benchmark run #333 has been queued from the fixed main branch.
- Coverage matrix #301 was cancelled when the follow-up commit arrived; corrected coverage run #302 is queued from the fixed main branch.
- Current live Worker probe on Foundation revision `c465ed8cff860cf0f1a1d6de6655aaf9594f02d2` has passed; new main-push runtime checks are queued against the newer repository head.
- Full L4 certification remains evidence-gated.

**Deployment authority:** Foundation GitHub Actions is the sole CI/CD and production deployment owner. Operations must remain without GitHub-hosted workflows. Do not re-enable Cloudflare Workers Builds or Deploy Hooks.

---