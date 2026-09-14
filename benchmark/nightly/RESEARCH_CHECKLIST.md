# Nightly Research Checklist

The nightly research system must behave as an incremental research program, not a repeated web crawl.

## 1. Per research task

Before starting a task:

- [ ] Assign a stable `task_id` and research question.
- [ ] Define the exact evidence needed.
- [ ] Load the previous research ledger.
- [ ] List sources already visited for this `task_id`.
- [ ] Mark sources that are still fresh enough to skip.
- [ ] Mark sources requiring revisit because of freshness, failure, or a new unresolved question.
- [ ] Generate a new-source queue from sources/domains not previously used for this task.

During the task, record every meaningful source visit:

- [ ] Source family: Reddit, retailer, OEM, YouTube, Amazon, Flipkart, Chinese community, professional review, GitHub, etc.
- [ ] Site/domain.
- [ ] Exact URL actually visited.
- [ ] Access method: search result, direct page, API, sitemap, feed, browser, repository, etc.
- [ ] Purpose: what evidence this source was expected to provide.
- [ ] Result: useful, duplicate, blocked, irrelevant, stale, contradictory, or failed.
- [ ] New evidence extracted.
- [ ] Product/entity/SKU/model affected.
- [ ] Citation/provenance recorded.
- [ ] Revisit policy assigned.

## 2. New-site rule

For the same `task_id`, prefer a previously unseen domain or exact source URL once a useful source has already been collected.

Do **not** repeatedly revisit a useful source merely because it is familiar.

A previously visited source may be revisited only when one of these is true:

1. The source has a freshness window that has expired.
2. The previous visit was blocked/transient/failed and retry policy allows another attempt.
3. New evidence indicates a contradiction that requires re-checking the source.
4. The research question changed materially.
5. A new product revision/model/region requires fresh evidence.
6. The source itself is known to change frequently, such as price, stock, news, or current community discussions.

## 3. Tomorrow's continuation

At the beginning of the next night:

- [ ] Load the prior ledger.
- [ ] Group prior visits by `task_id`.
- [ ] Exclude sources already visited and still fresh.
- [ ] Promote unresolved findings into follow-up tasks.
- [ ] Convert failed/blocked sources into retry candidates only when policy permits.
- [ ] Prioritize previously unseen sites/domains for each task.
- [ ] Avoid repeating identical queries unless needed for validation.
- [ ] Keep old evidence for historical comparison; do not delete it just because it is no longer current.
- [ ] Record every new visit back into the new night's ledger.

## 4. Task completion gate

A research task is not complete merely because pages were visited.

- [ ] Required source families attempted.
- [ ] New-site exploration performed.
- [ ] Important contradictions checked.
- [ ] Old-vs-new evidence reconciled when relevant.
- [ ] Useful findings linked to exact sources.
- [ ] Blocked/unreachable evidence documented.
- [ ] New techniques or alternative approaches recorded.
- [ ] Benchmark/regression test candidates captured.
- [ ] Follow-up work generated for the next night.

## 5. Morning report must answer

- What tasks ran?
- Which sites/domains were visited for each task?
- Which were new compared with previous nights?
- Which sources were deliberately skipped and why?
- What evidence was found?
- What evidence was contradictory or stale?
- Which sources were blocked/unreachable?
- What new technique or platform behavior was discovered?
- What benchmark failed or regressed?
- What should be researched next night?

## 6. Tracking principle

The unit of deduplication is **`task_id + canonical source URL`**, not the domain alone.

The unit of novelty is **new useful evidence**, not simply a new URL.

The system should therefore avoid both repeated browsing and artificial novelty: a new page that only repeats an already-known claim is recorded as a duplicate finding.