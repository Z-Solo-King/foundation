# Family Full Coverage Standard — 2026-10-01

## Purpose

This is the structural completeness layer for the Foundation/Operations family.

It is deliberately narrower than the existing six-lane exhaustive audit: it answers one question — **did we enumerate every Git-tracked file, classify it, and confirm the critical cross-system surfaces still have their declared anchors?**

The standard covers the application and control-plane surfaces that are easy to miss when auditing by feature name alone: chatbot, extractor/mapper, feed recovery, search, research/evidence, AI maps, documentation/structure/format, Cloudflare runtime and AI/browser, Backblaze B2, APIs, provider policy, security/identity/resources, artifacts/schemas, polyglot languages, learning/memory/maintenance, autonomous control-plane, and GitHub MCP/App/Actions governance.

## 100% definition

100% is a structural claim only:

- every Git-tracked file in each supplied repository is visited;
- every file receives exactly one primary audit surface;
- no tracked file is silently ignored because of extension;
- all declared critical functional anchors exist;
- MCP remains discovery-only with no runtime dependency;
- Marketplace Apps remain disabled/zero-installed under the strict $0 policy;
- every current GitHub Action ref is checked by the existing immutable-SHA and zero-cost validator.

This does **not** mean 100% runtime correctness. Runtime acceptance remains owned by the existing evidence, live-probe, migration, release, feed, and research gates.

## Current family scope

The matrix contains the full repository tree classification for Foundation and Operations plus explicit functional surfaces and external ecosystem controls. The classifier uses `git ls-files`, so the denominator is the repository's tracked Git surface rather than filesystem noise.

## External ecosystems

### MCP

MCP repositories are engineering references only. No MCP package is added to the runtime. Useful patterns are translated into local contracts for semantic context, browser interaction/diagnosis, bounded tools, document normalization, and negative-path testing.

### GitHub Apps

The supplied Marketplace Apps workbook is represented as 1,408 entries. Apps that require paid plans, paid trials, payment methods or external billing are outside the project policy. Marketplace installation remains disabled by default.

### GitHub Actions

The supplied Marketplace Actions workbook is represented as 9,999 entries. Discovery is not installation. Current repository Action usage is governed by exact immutable SHAs, standard public runners, no Docker Actions, and explicit zero-cost policy validation.

## Domain rule

One function may touch many surfaces; primary classification is only an inventory mechanism. Functional correctness remains checked by the specialized tests and evidence systems already in the repositories.

The existing six-lane audit remains the deeper semantic audit. This coverage validator is its completeness guard, not a replacement authority.
