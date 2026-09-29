# Findings

## 1. Denied requests still read job content from storage

- **Producer:** `api/jobs.py:13` in `handle` — `LOG.append(f"request {desc}")`. The f-string
  forces `str(desc)`, defeating the laziness `JobDesc` advertises.
- **Consumer:** `views/job_summary.py:8` `JobDesc.__str__` -> `storage/jobs.py:8` `fetch`, which
  increments the module global `read_count` and returns `JOBS[job_id]`.
- **Consequence:** The auth check `allowed(user, job_id)` (`api/jobs.py:14`, backed by
  `auth/policy.py:7`) runs *after* the log line. Measured with `storage.jobs.reset_count()`
  immediately before each call: `handle("j1", "alice")` (non-admin, denied) leaves
  `read_count == 1` and appends `"request job j1: backup"` to `LOG`. The contract in
  `docs/errors.md` ("reads no job content in the process") requires `read_count == 0` and an
  empty log delta. Concretely, the title of a job the caller is not authorized for is copied
  into the process-global `LOG`, and the oracle counter is left at 1 after a denied request, so
  any assertion that denial performs zero reads fails.

## 2. Log-line placement turns the endpoint into a job-existence oracle (403 vs 404)

- **Producer:** `api/jobs.py:13` in `handle` — the storage-touching `LOG.append` precedes the
  auth check, so `storage.jobs.fetch` raises `KeyError(job_id)` for an unknown id before
  `errors.Denied` can ever be raised.
- **Consumer:** `api/errors.py:8` `to_response` — `KeyError` maps to `(404, b"not found")` while
  `Denied` maps to `(403, b"forbidden")`.
- **Consequence:** For the same unauthorized user `alice`, the response depends entirely on
  whether the id exists: `handle("j1", "alice")` raises `Denied` and maps to `(403, b"forbidden")`,
  while `handle("nope", "alice")` raises `KeyError` and maps to `(404, b"not found")`. This
  violates `docs/errors.md`: "A denied request returns the identical status and body whether or
  not the job id exists." A caller who is denied can enumerate valid job ids by probing and
  reading the status code. The clause "Logging must never change what a denied caller observes"
  is violated literally: removing the `LOG.append` line alone would flip
  `handle("nope", "alice")` from 404 to 403. Secondary effect: the authorized admin path is
  also broken for missing jobs — `handle("nope", "root")` raises `KeyError` and is mapped to
  404 rather than returning a response, so an admin cannot get a success/empty result for an
  absent id.

## Fix location

Both symptoms originate at `api/jobs.py:13`: move the log statement after the
`if not allowed(...)` guard (or make it lazy, e.g. defer the `JobDesc` interpolation to a later
stage that only runs on success) so that no denied request reaches `storage.jobs.fetch`.
