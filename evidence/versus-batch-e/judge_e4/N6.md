# Findings

## F1 — Auth decision is taken after job storage I/O and a log write

**Producer:** `api/jobs.py:13` — `handle`, the `LOG.append(f"request {desc}")` statement.

**Consumer:**
- `views/job_summary.py:8-11` — `JobDesc.__str__`, which runs the deferred import of `storage.jobs.fetch` and reads `info['title']`.
- `storage/jobs.py:8-13` — `fetch`, which increments `read_count` and raises `KeyError(job_id)`.
- `api/errors.py:8-13` — `to_response`, which maps that `KeyError` to `(404, b"not found")`.
- The declared contract in `docs/errors.md:3-5`.

**Consequence:** `api/jobs.py:13` is evaluated before the `if not allowed(user, job_id)` guard on line 14. The f-string is not lazy — it calls `JobDesc.__str__`, which performs a real storage read. Three observable effects, each a direct violation of `docs/errors.md`:

1. **A denied request reads job content.** `handle("j1", "alice")` drives `storage.jobs.read_count` from `0` to `1` and writes `"request job j1: backup"` into `LOG` — the title of a job the caller was not authorized to see is copied into the process log. The contract requires that a denied request "reads no job content in the process." The job `j1` in `storage/jobs.py:4` has `owner: "ops"`; user `alice` is not that owner and is not in `ADMINS`, yet the title `backup` still reaches the log.

2. **Denied responses differ by job existence, breaking the identical-response rule.** Verified output:

   | call | result | `read_count` | `LOG` |
   |---|---|---|---|
   | `handle("j1", "alice")` (denied, job exists) | `(403, b"forbidden")` | `1` | `['request job j1: backup']` |
   | `handle("missing", "alice")` (denied, job absent) | `(404, b"not found")` | `1` | `[]` |
   | `handle("j1", "root")` (allowed) | `{"ok": True}` | `1` | `['request job j1: backup']` |

   `docs/errors.md` requires the identical status and body "whether or not the job id exists." Instead the body is `not found` versus `forbidden`, so any caller can probe job existence through an endpoint that should not disclose it.

3. **The authorization check is skipped entirely for unknown ids.** Because `fetch` raises `KeyError` on line 12 of `storage/jobs.py`, `handle` never reaches line 14. `allowed("alice", "missing")` is never called at all. Authorization is a function of whether the job exists, not of who is asking.

**Risk band:** R4 (critical boundary — authorization). Per `references/semantic-risk.md`, evidence is complete here, so this is reported with a concrete correction rather than deferred, but the fix must preserve the `LOG` format string and the `(403, b"forbidden")` / `(404, b"not found")` bodies exactly, since `references/error-reliability.md` treats that text as observable behavior. The minimal correction is to move the `LOG.append` statement below the `if not allowed(...)` guard — that alone removes the storage read and the `KeyError` from the denied path, and makes both denied responses `(403, b"forbidden")` with `read_count == 0`. Whether the `LOG` entry should be emitted at all for allowed callers (and whether a non-lazy `str(desc)` should be used) is a policy question for the API owner, not a safe inference here.

## F2 — Access policy ignores the `job_id` it is handed, and the storage `owner` field has no reader

**Producer:** `auth/policy.py:7-8` — `allowed(user, job_id)`, which returns `user in ADMINS` and never reads `job_id`.

**Consumer:** `storage/jobs.py:4` — `JOBS = {"j1": {"title": "backup", "owner": "ops"}}`; the `owner` key is written and read by nothing in this fixture. `api/jobs.py:14` is the only caller and passes the id positionally.

**Consequence:** The observable effect is an authorization model that is `ADMINS` only. `handle("j1", "ops")` returns `(403, b"forbidden")` even though `ops` is the recorded owner of `j1`, while `handle("j1", "root")` succeeds for every job regardless of owner. The unused `job_id` parameter and the unread `owner` field are the two halves of the same gap: if owner-based access is intended, `ops` is locked out of their own job.

**Deliberately reported, not proposed for change.** I could not establish which model is intended: `docs/errors.md` is the only normative document present and it specifies only the denied-response shape, not who is granted access. Owner-based grant and admin-only deny are both consistent with every artifact in this fixture, and `references/semantic-risk.md` classifies authorization as R4 where incomplete evidence means preserve behavior and report. Adding an owner check would be a guess that changes access for existing callers. This finding needs a decision from the policy owner, and no source change should be made on the strength of it alone.
