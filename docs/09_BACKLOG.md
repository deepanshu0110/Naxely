# Naxely — Backlog Notes (unscoped)

> Tier: "someone noticed, nobody's confirmed impact, don't scope yet."
> Items here are records of observations, not commitments. Do not plan work from
> this file without first confirming impact and scoping.

---

## B-001 — Bar-chart caption quotes full category names verbatim

- **Status:** noted 2026-08-04, not investigated, not confirmed to break anything.
- **Observation:** categorical bar chart captions in `chart_service.py`
  (the "X tops Y at N; Z trails at M" pattern) quote category names in full,
  including long ones — a 40-char category name appeared unshortened in
  Phase 2 evidence output.
- **Class:** same general family as the insight/anomaly/table truncation bugs,
  but for category *names* rather than long-form *text*.
- **Unconfirmed:** whether a long category name can actually break layout
  (PDF caption width, PPTX slide) or only looks ungainly.

## B-002 — Supabase partial-write / retry without upsert flag

- **Status:** noted 2026-08-04, unverified, low confidence.
- **Observation:** if a `storage.upload` request (PDF or PPTX) is interrupted
  after Supabase partially accepts the object, a partial object could linger at
  the storage path. A retry's `storage.upload` call passes no upsert flag
  (`report_service.py:298-301`, `reports.py:1001-1003`), so the retry could
  fail with FileExists instead of overwriting.
- **Unconfirmed:** Supabase's actual partial-write behavior was not tested;
  the failure path may never occur in practice.
