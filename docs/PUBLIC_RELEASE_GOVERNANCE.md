# Public release governance

## Feed distribution boundary

WooCommerce/Google XML recovery output is an internal workflow artifact. It must never be distributed through a GitHub Release, release asset, public release tag, or release download URL.

The prohibited feed release identifier is `wc-google-feed-latest`. It must not appear in feed workflows.

Feed workflows may request only read access to repository contents. They must not invoke release creation, release upload, release edit, release actions, tag-push publication, or release download URLs.

## Merge gate

The required `Public tests` check executes `scripts/validate_release_publication_policy.mjs`. The policy scans workflow and executable repository surfaces and fails on prohibited publication primitives.

Because `Public tests` is one of the repository's required main-branch status checks, reintroducing an automated public feed release path is a merge-blocking policy violation.

## Defense in depth

`.github/workflows/feed-release-governance.yml` repeats the policy on pull requests and main/scheduled execution. On main/scheduled execution it has a narrowly scoped cleanup permission used only to remove the specifically prohibited `wc-google-feed-latest` release and tag if they somehow reappear.

The supported distribution/evidence mechanism for feed bundles is GitHub Actions workflow artifacts.
