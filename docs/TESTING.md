# Papery — Test & Hardening Log

This document records the automated test campaign run against a live stack
(PostgreSQL + FastAPI + Next.js) and the bugs it surfaced and fixed. It is
meant to be reproducible and extended as the product grows.

## Test layers

| Layer | What it covers | Where |
|---|---|---|
| **Unit** | normalization, classification, extraction, comparison, match quality | `backend/tests/` (33 tests) |
| **API contract & security** | all endpoints, RBAC, license/quota gates, tenant isolation, hostile inputs | scripted HTTP sweep (52 checks) |
| **Document workload** | PDF/DOCX/PNG/TIFF, multi-page, 300-page, corrupt, disguised, oversized | scripted HTTP sweep (15 checks) |
| **Concurrency** | parallel verifications, quota race, memory | scripted load test |
| **Browser E2E** | full user journey in real Chromium | Playwright (20 checks) |

## Verified behaviors (highlights)

- **Auth/RBAC:** wrong password, garbage/expired tokens, refresh-token type
  confusion, staff vs manager vs admin permissions, "can't modify own account".
- **Tenancy isolation:** company B cannot read/verify/patch company A's
  files, verifications, or findings (all 404); staff see only their own.
- **License & quota:** dashboard gated without active license (402); seat
  limit enforced; monthly document quota enforced — and **race-proof** under
  12 parallel requests (never exceeds the cap).
- **Documents:** digital PDF, DOCX, PNG/TIFF (OCR), 5-page and 300-page PDFs
  all process; corrupt / disguised / oversized inputs never silently PASS.
- **Match quality:** on a 19-case real-world probe, **0 false positives and
  0 false negatives** (dates in mixed formats, punctuation spacing, OCR
  confusions, fuzzy near-misses).
- **Multi-container B/Ls:** every container/seal row is extracted and compared
  as a set, so a wrong/missing/extra container or seal on any row is caught —
  not just the first row.
- **Numbers:** US and EU grouping (`1,234.50` and `1.234,50`) normalize equal.
- **Reports:** PDF, Excel, and JSON contain the correct findings, values,
  severities, and suggested fixes (not just correct MIME types).
- **Resilience:** killing the server mid-verification leaves an actionable
  FAILED state on restart, not a stuck spinner.
- **Security:** SQL-injection and XSS payloads in titles/search are
  parameterized and escaped; path-traversal filenames cannot escape storage;
  100-verification soak shows flat memory (no leak) and p95 latency ~0.34s.

## Bugs found and fixed during the campaign

1. **Quota race condition** — concurrent verification creates duplicated the
   usage-counter row and lost increments, allowing quota bypass. Fixed with a
   `UNIQUE(company_id, period_start)` constraint plus upsert + `SELECT ... FOR
   UPDATE` in the same transaction. *(commit: concurrency-safe usage counting)*
2. **Stuck verifications after a crash** — background tasks die with the
   process, leaving rows PROCESSING forever. Added startup recovery that marks
   interrupted work FAILED with a clear message. *(commit: recover interrupted
   verifications)*
3. **False-positive alerts** — mixed date formats (`2026-02-10` vs
   `10/02/2026`) and punctuation spacing (`CO., LTD` vs `CO.,LTD`) were flagged
   as mismatches. Added unambiguous-anchored date equivalence and
   punctuation-tolerant text normalization. *(commit: eliminate false-positive
   alerts)*
4. **Phantom id fields** — a heading like "BOOKING CONFIRMATION" made the bare
   "booking" alias capture "CONFIRMATION". id/number/date fields now require a
   digit — in both the line-based extractor and the layout-aware extractor's
   low-confidence fallback. *(commits: reject digit-less matches; gate spatial
   fallback to text-only)*
5. **Seat-limit race** — concurrent team invites bypassed `max_users` (10
   parallel creates → 11 users on a 3-seat plan). Fixed by locking the company
   row before the count + insert. *(commit: concurrency-safe seat-limit)*

## Reproduce

Bring up a local stack (`docker compose up --build`), then run the unit suite:

```bash
cd backend && pytest -q
```

The scripted HTTP/E2E sweeps live in the session scratchpad; port them into
`backend/tests/` (API) and a Playwright project as the suite is formalized.
