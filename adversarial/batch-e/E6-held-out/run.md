# E6 run: expiring flags (held-out, never used for tuning)

Symptom prompt (all arms get ONLY this): "feature flags need expiry."

- Fixture: `fixture/` — flag store without TTL (`add(name, enabled)` only),
  `query.active_flags`, `FLAGS.md` with no TTL section.
- Task: optional `expires_at`, boundary `now < expires_at`, `purge_expired(now)`
  returning the removed count (idempotent), `active()` respects expiry, docs updated.
- Evaluator: `evaluator/test_expiry.py`, `FIXTURE_DIR` selects variant, separate processes.
- Solution: `solution/` (TTL field, strict `<`, stage-free purge, documented).

## Validation log

1. Baseline: 4 failed (TypeError on the missing kwarg + docs), 1 passed
   (`unknown stays false` — pre-existing behavior, correctly preserved by the fix).
2. Solution: 5 passed.
3. Mutants (`<=` boundary, count-without-delete, /tmp, deleted): 3 failed —
   boundary and idempotency checks have teeth.
4. Held-out status: new flags domain, never referenced by any skill patch or prior
   fixture. First arms contact happens in the next blind round.

Arms protocol: A0 bare / A1 superpowers-4 / A2 ours (SKILL.md + shared-contracts +
evolution + migration-examples), least-privilege dirs. Watch for: breaking the
unknown-name contract, `<=` boundary slip, non-idempotent purge, missing docs.
