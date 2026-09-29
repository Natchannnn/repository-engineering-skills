# Findings

Fixture contract under test: `docs/errors.md` — "A denied request returns the identical
status and body whether or not the job id exists, and reads no job content in the
process. Logging must never change what a denied caller observes."

All three findings below were reproduced by executing the fixture in-place
(`python -c` with this directory on `sys.path`); the observed values quoted are actual
output, not inferred. No file other than this one was modified.

---

## 1. Request is stringified (and therefore reads job content) before the auth check

- **Producer:** `api/jobs.py` — `handle()`, line 13: `LOG.append(f"request {desc}")`,
  where `desc = JobDesc(job_id)` from `views/job_summary.py`.
- **Consumer:** `views/job_summary.py` — `JobDesc.__str__`, line 10: `info = fetch(self.job_id)`
  → `storage/jobs.py` — `fetch()`, which returns the full record `{"title": "backup", "owner": "ops"}`.
  The authorization gate `auth.policy.allowed(user, job_id)` at `api/jobs.py:14` runs *after* this.
- **Consequence:** For a denied caller, job content is fetched, materialized, and copied into
  the process-wide log before `errors.Denied` is ever raised. Observed for
  `handle("j1", "alice")`: `storage.jobs.read_count == 1` and
  `api.jobs.LOG == ["request job j1: backup"]` — the secret field `title` ("backup") and the
  `owner` record are disclosed in `LOG` to a caller that is denied authorization and receives
  only `403 forbidden`. The deferred import inside `__str__` is cosmetic; the I/O happens on
  every stringification, so the f-string on line 13 triggers it on every request.
  This directly violates the normative clause "reads no job content in the process" and
  "Logging must never change what a denied caller observes."

## 2. Pre-auth stringification raises `KeyError` for unknown ids, turning `Denied` into a 404 existence oracle

- **Producer:** `storage/jobs.py` — `fetch()`, line 12: `raise KeyError(job_id)`, reached
  unconditionally from `api/jobs.py:13` before the `allowed()` check on line 14.
- **Consumer:** `api/errors.py` — `to_response()`, lines 11-12: `isinstance(exc, KeyError)` →
  `(404, b"not found")`; `Denied` (line 9-10) → `(403, b"forbidden")`. Because the `KeyError`
  escapes `handle()` first, the `Denied` branch is never reached for an unknown id.
- **Consequence:** Identical denied status/body is not produced. Observed pair for the same
  unauthorized user `alice`:
  - `handle("j1", "alice")` → `(403, b"forbidden")`
  - `handle("nope", "alice")` → `(404, b"not found")`
  A caller with no access to any job can enumerate which job ids exist (404 = absent,
  403 = present). The contract requires `(403, b"forbidden")` in both cases.

## 3. The `read_count` oracle is incremented by every request, including fully denied ones and the 404 path

- **Producer:** `storage/jobs.py` — `fetch()`, lines 9-10: `read_count += 1` happens *before*
  the `job_id not in JOBS` existence check, so the counter is charged even on the branch that
  raises and returns no data.
- **Consumer:** `api/jobs.py` — `handle()`, line 12-13, constructs `JobDesc` and stringifies it
  before authorization, so the charged read belongs to a request that never gets served.
- **Consequence:** `storage.jobs.read_count` is `1` for *every* request shape, including the
  ones the contract says read nothing. Observed with `reset_count()` before each call:
  - `handle("j1", "root")` → `read_count == 1` (correct: a read is legitimate here)
  - `handle("j1", "alice")` → `read_count == 1`, result `(403, b"forbidden")` — should be `0`
  - `handle("nope", "alice")` → `read_count == 1`, result `(404, b"not found")` — should be `0`
  - `handle("nope", "root")` → `read_count == 1`, result `(404, b"not found")` — should be `0`
  The counter therefore cannot distinguish "authorized read" from "content pulled out of storage
  for a caller that was then rejected", and in the `nope` case the increment persists even though
  `LOG` is empty and the record was never returned — a side effect with no corresponding log entry.

---

## Verification appendix (evidence, not a finding)

Reproduced in-place with the fixture's own modules; exact output:

```
root/j1     -> (('OK', {'ok': True}), 1, ['request job j1: backup'])
alice/j1    -> ((403, b'forbidden'), 1, ['request job j1: backup'])
alice/miss  -> ((404, b'not found'), 1, [])
root/miss   -> ((404, b'not found'), 1, [])
```
(tuple = `to_response(handle(...))`, `storage.jobs.read_count`, `api.jobs.LOG`)

Scope limits, stated rather than searched past: the fixture contains no test files, no
package/test config, and no VCS metadata, so there is no existing suite to run and no
regression test that would have caught findings 1-3. `api/errors.to_response` has no call
site anywhere in the fixture — the mapping in findings 2 was exercised by calling it directly,
so whether production code actually routes handler exceptions through it is unverified here.
`auth.policy.allowed(user, job_id)` ignores its `job_id` parameter; that is a plausible
simplification rather than a demonstrable defect, so it is not listed as a finding.
