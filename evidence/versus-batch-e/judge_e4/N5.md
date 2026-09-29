# Findings

## F1 — False defect annotation on the pre-auth log line invites a behavior-neutral "fix" to correct code

**Producer:** `api/jobs.py:13`, in `handle` — trailing comment on
`LOG.append(f"request {desc}")`:

```python
LOG.append(f"request {desc}")  # BUG: f-string evaluates BEFORE the auth check
```

**Consumer:** `api/jobs.py:14` `if not allowed(user, job_id)` → `raise errors.Denied()`,
consumed by `api/errors.py:8` `to_response` (maps `Denied` → `(403, b"forbidden")`);
the contract being referenced is `docs/errors.md` (denied request must return identical
status/body whether or not the job id exists, read no job content, and be unaffected by
logging). `views/job_summary.py:9` `JobDesc.__str__` is the stringification the comment
blames.

**Consequence:** The comment asserts a defect that does not exist. The claim is a
statement about *evaluation order* (the f-string does run before the auth check), but
evaluation order is only harmful if the f-string performs I/O — and `JobDesc.__str__`
returns `f"job {self.job_id}"` from data the descriptor already holds, with no call into
`storage/jobs.py:fetch`. Verified by execution across the four (user, job_id) cases:

| user | job_id | result | `storage.jobs.read_count` |
|------|--------|--------|--------------------------|
| bob  | j1     | `(403, b'forbidden')` | 0 |
| bob  | missing| `(403, b'forbidden')` | 0 |
| root | j1     | `{'ok': True}`        | 0 |
| root | missing| `{'ok': True}`        | 0 |

Both denied cases are byte-identical in status and body, and no denied path reads job
content — exactly what `docs/errors.md` requires. The concrete cost is not a runtime
failure; it is that the annotation is an unowned, unverifiable claim sitting on a line
that a future maintainer will treat as a known bug. Acting on it invites changes that
are provably no-ops under this fixture (reordering the append after `allowed()`, or
deferring to a lazy `__str__`), each of which is churn against a contract that is
already satisfied, and each of which risks a real regression if the author concludes the
"fix" must also suppress the `LOG` entry — that would change what the endpoint emits for
denied callers, which `docs/errors.md` explicitly forbids. Per the evidence gate, a
comment that cannot survive a five-minute execution check should not be treated as
precedent for a source change. Minimal correction: delete the `# BUG:` annotation (or
replace it with the invariant it should have recorded — that `JobDesc` stringification is
I/O-free by design, which is the non-obvious fact worth preserving here). No change to
`handle`'s control flow is warranted; the current order is correct.
