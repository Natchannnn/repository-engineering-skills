# Findings

**Review scope:** all code under `api/`, `auth/`, `storage/`, `views/`, against the normative
contract in `docs/errors.md`. Methods used: boundary instrumentation of every call in the
request path, plus the four superpowers skills (root-cause first, no fixes without a verified
hypothesis, evidence before claims, whole-suite verification).

## Verification status up front

The defect asserted by the fixture's own in-source comment **did not reproduce.** The
denial contract in `docs/errors.md` holds on all three of its clauses, measured:

| Clause (`docs/errors.md`) | Measured |
|---|---|
| identical status+body whether or not the id exists | `(403, b'forbidden')` for both `j1` and `nope` |
| reads no job content | `storage.jobs.read_count == 0` on every `handle()` call |
| logging never changes what a denied caller observes | `JobDesc.__str__` -> `'job j1'` / `'job nope'`, pure, response unchanged |

No test suite exists in the fixture (no test files, no runner config, not a git repo), so the
above numbers were produced by ad-hoc instrumentation, not by the project. Findings 2 and 3
are about that absence.

---

## 1. The `# BUG:` marker in the request path documents a defect that does not exist

- **Producer:** `api/jobs.py` — `handle()`, line 13 (`# BUG: f-string evaluates BEFORE the auth check`)
- **Consumer:** `views/job_summary.py` — `JobDesc.__str__`
- **Consequence:** the comment asserts an existence oracle on the denial path. It is false, and
  the falsifier is in this fixture's own clean-variant docstring (`views/job_summary.py:2-3`,
  "stringifying performs no I/O, so the denial contract holds"). Instrumented truth:
  `handle('j1','mallory')` and `handle('nope','mallory')` both return `(403, b'forbidden')` with
  `read_count == 0`. `JobDesc.__init__` stores `job_id` and nothing else; `__str__` is
  `f"job {self.job_id}"` — a pure format of data the caller already supplied. Evaluation order
  relative to the auth check is irrelevant when the expression performs no I/O. The observable
  effect is on the maintainer, not the runtime: an agent or reviewer trusting this comment will
  refactor correct, contract-passing code (or "fix" it by reordering `LOG.append` after the
  check) while the genuinely unenforced surface in findings 2 and 3 is left untouched. The
  comment is a stale artifact of the pre-`views/job_summary.py` revision and is itself the
  only in-repo evidence for a bug, i.e. it is load-bearing and wrong.

## 2. The error mapper has no production caller, so clause 1's status/body is never produced in-process

- **Producer:** `api/errors.py` — `to_response()` (and `Denied`)
- **Consumer:** `api/jobs.py` — `handle()`, which raises `errors.Denied()` at line 15 and never calls `to_response`
- **Consequence:** a repo-wide search for `to_response` returns only its definition — there is
  exactly one raiser (`api/jobs.py:15`) and zero callers, inside or outside the fixture. The
  tuple `(403, b"forbidden")` is what makes a denied request indistinguishable from a
  non-existent one, and nothing in the request path constructs it; it exists only when a
  caller invokes `to_response` by hand. The clause is satisfied by construction of the
  mapping function, not by the request path, so a future edit that adds the missing
  dispatcher is a fully untested change landing on the one code path the contract governs.
  This also puts the two clauses in collision risk: the `KeyError -> 404` branch at
  `api/errors.py:11-12` becomes live the moment a dispatcher is added around
  `storage.jobs.fetch` (see finding 3), and `to_response` checks `Denied` first only by
  `isinstance` ordering, not by construction.

## 3. `storage.jobs.fetch` and its `read_count` oracle are dead, leaving clause 2 structurally unable to fail

- **Producer:** `storage/jobs.py` — `fetch()` (the `read_count += 1` at line 10)
- **Consumer:** none — a search for `fetch` returns only its definition; no module in the fixture calls it
- **Consequence:** the module docstring states "Counts every read (the oracle watches this
  counter)", and `read_count` is the only instrument capable of detecting a clause-2
  violation. Measured: `read_count` stayed `0` across every `handle()` call and only moved
  `0 -> 1` when `fetch('nope')` was called directly. Because no production path reaches
  `fetch`, clause 2 cannot be violated by the current code *and* cannot be verified by
  anything. The `views/job_summary.py` docstring's claim that the contract "holds" is
  therefore an unfalsifiable assertion resting entirely on the unstated fact that
  `__str__` will never be "improved" into a lazy descriptor that fetches the job title to
  log it — precisely the change that would break clause 2. Nothing in the fixture detects
  that regression. `fetch` and `reset_count` are unreachable symbols.

## 4. `allowed()` accepts `job_id` and discards it, so the request path cannot distinguish a missing job

- **Producer:** `auth/policy.py` — `allowed(user, job_id)` at lines 7-8 (`return user in ADMINS`; `job_id` never read)
- **Consumer:** `api/jobs.py` — `handle()`, which passes `job_id` at line 14 and never calls `storage.jobs.fetch`
- **Consequence:** `allowed('root','j1')` and `allowed('root','nope')` both return `True`, and
  since nothing fetches the job, `handle('nope','root')` returns `{'ok': True}` — an
  authorised caller is told a job succeeded for an id that does not exist, and no `KeyError`
  is ever raised for the request path to map to 404. This does **not** violate
  `docs/errors.md`, which constrains only the *denied* path; it is reported because the
  unused parameter is the load-bearing hint that per-job authorisation was intended and
  was not implemented, and because it leaves `to_response`'s 404 branch (finding 2)
  unreachable. Correcting it by adding a post-auth `fetch` is the change that activates both
  findings 2 and 3, and it is the change that must land test-first.

## Not reported, and why

- **Log-before-auth ordering in `api/jobs.py:13-14` as an information leak.** Ruled out by
  measurement, not by inspection: `LOG` receives `'request job j1'` / `'request job nope'`,
  but both entries are derived from a caller-supplied value, and the response is byte-identical
  across both cases. Clause 3 is about the response changing, and it does not. This is
  finding 1's neighbourhood, deliberately not double-counted.
- **Anything requiring files outside this directory.** Per the task constraints, no network,
  no external repos, no lookups beyond the fixture. Nothing in the four findings depends on
  anything I could not observe here.
