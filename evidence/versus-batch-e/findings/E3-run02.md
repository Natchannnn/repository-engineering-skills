# Findings

Review scope: `ledger/`, `transport/`, `wire/`. Verified by executing the real
modules (Python 3.14.5); every "observed" line below is captured program output,
not inference.

**No test suite exists in this fixture** (`python -m pytest --collect-only` →
`collected 0 items`; no `test_*.py`, no `conftest.py`, no `pyproject.toml`/
`setup.py`/`pytest.ini`). Per the TDD skill none of the code below was developed
test-first — no regression test exists for any of these paths. Findings are
ordered by severity.

---

## 1. Dedup keyed on whole-byte payload ignores the receipt's own `id`, so a re-serialized duplicate is applied twice

- **Producer:** `wire/receipt.py:6` — `make_receipt(tx_id, amount)` emits a
  payload containing an explicit transaction identity field, `"id": tx_id`.
- **Consumer:** `ledger/dedup.py:8` — `already_applied(raw)` computes
  `sha256(raw)` over the *entire* byte string and never inspects the `id`. The
  identity field the producer writes is dead weight to the guard that is supposed
  to enforce exactly-once.
- **Consequence:** Two byte strings that denote the *same* transaction are two
  distinct dedup keys, and the balance double-counts. Because
  `make_receipt` passes `amount` through to `json.dumps` unconverted, the same
  logical receipt serializes two different ways depending only on the caller's
  Python type for the amount:

  ```
  apply(wrap(make_receipt('tx-1', '10.00')))  ->  Decimal('10.00')
  apply(wrap(make_receipt('tx-1',  10.00))   ->  Decimal('20.00')   # double-applied
  make_receipt('tx-1','10.00') == make_receipt('tx-1',10.00)  ->  False
  ```

  One transaction `tx-1` for 10.00 is counted as 20.00. The replay guard's
  module docstring ("Replay guard keyed on the SHA-256 of received BYTES") and
  `receipt.py`'s ("BYTES ARE THE DEDUP IDENTITY") agree with each other but
  contradict the data model: `id` is the identity, and the byte hash is a
  function of `amount` and `note` as well. Any re-serialization that differs by
  whitespace, key order, escaping, or a retried/ corrected amount silently
  bypasses the guard. Root cause is the *producer* failing to canonicalize
  `amount`; the consumer amplifies it by trusting a content hash as identity.

## 2. Producer passes `amount` to `json.dumps` unconverted; consumer re-reads it as a float, corrupting the `Decimal` balance

- **Producer:** `wire/receipt.py:7-8` — `make_receipt` places the caller's
  `amount` object straight into `json.dumps(...)`. A float becomes a JSON
  *number*, and `json.loads` on the other end returns it as a Python float.
- **Consumer:** `ledger/apply.py:18` — `balance += Decimal(data["amount"])`.
  `Decimal(float)` converts the exact binary value, not the decimal literal the
  producer intended.
- **Consequence:** a tenth of a currency unit lands in the money balance as
  binary-float noise:

  ```
  make_receipt('t1', 0.1)  ->  b'{"amount":0.1,"id":"t1","note":"caf\u00e9"}'
  apply(wrap(...))         ->  Decimal('0.1000000000000000055511151231')   # 28 fractional digits
  balance == Decimal('0.1') ->  False
  ```

  `ledger/apply.py:9` initialises `balance = Decimal("0.00")` and
  `apply` accumulates into it, so this error is permanent and compounding: after
  100 such receipts the balance carries ~5.5e-16 of phantom value per receipt.
  The consumer is defensible in accepting both `str` and numeric JSON (that is
  what makes finding 1 reachable), so the fix belongs at the producer boundary —
  emit `amount` as a string so `Decimal(data["amount"])` round-trips.

## 3. Replay guard records the hash before the apply can succeed, so a failed receipt is permanently swallowed

- **Producer:** `ledger/dedup.py:8-13` — `already_applied` *inserts* the digest
  into the module-level `_seen` set (line 12) as a side effect of the check, and
  returns `False` to let the caller proceed.
- **Consumer:** `ledger/apply.py:15-18` — `apply` trusts that `False` and only
  then does `json.loads` and `Decimal(data["amount"])`, both of which can raise.
  There is no rollback of the recorded digest on failure.
- **Consequence:** a receipt that fails to apply is marked as already-applied
  anyway. The exception surfaces once, then the identical receipt is silently
  discarded forever, with a return value indistinguishable from a successful
  duplicate:

  ```
  1st apply(wrap(b'{"id":"tx-2","amount":"not-a-number"}'))  ->  RAISED InvalidOperation
  2nd apply(wrap(same bytes))                               ->  Decimal('0.00')   # silently dropped
  len(dedup._seen)                                          ->  1                 # marked applied
  ```

  Balance is unchanged and the caller receives `Decimal('0.00')` as though
  nothing were wrong. That receipt can never be applied by any retry, because the
  only way to clear the set is `ledger/apply.py:22` `reset()`, which discards the
  entire balance as well. Lost transaction, no error signal — a correctness
  failure worse than the crash it replaces. Check and commit of "applied" must be
  a single operation performed *after* the amount is booked.

## 4. Envelope `encoding` field is written by the producer and read by nobody; payload decoding is hardcoded UTF-8

- **Producer:** `transport/envelope.py:4-5` — `wrap` stamps every envelope with
  `"encoding": "utf-8"`, declaring the payload's byte encoding as metadata.
- **Consumer:** `transport/envelope.py:8-9` — `unwrap` returns `env["payload"]`
  and never reads `env["encoding"]`; `ledger/apply.py:17` then hardcodes
  `raw.decode("utf-8")`. No component in the package consumes the declared
  encoding.
- **Consequence:** the declared encoding is inert, so any payload that is not
  UTF-8 — including one the producer correctly labelled as such — crashes
  downstream in the ledger rather than being decoded as advertised:

  ```
  env = {'payload': b'{"id":"t4","amount":"1.00","note":"caf\xe9"}', 'encoding': 'latin-1'}
  unwrap(env) == env['payload']   ->  True        # declared encoding discarded
  apply(env)                     ->  UnicodeDecodeError: 'utf-8' codec can't decode
                                      byte 0xe9 in position 43: invalid continuation byte
  ```

  The one non-ASCII character in the fixture's own receipt vocabulary (`"café"`,
  `wire/receipt.py:7`) is exactly what trips this, since it is the only byte
  outside ASCII in the payload. `wrap`'s contract is unverified and unenforced;
  the decode belongs at the layer that owns the encoding claim.

---

## Not filed (checked, no defect)

- `ledger/apply.py:9` module-global `balance` and `ledger/dedup.py:5` module-global
  `_seen` are shared mutable state, and the check-then-add in
  `already_applied` plus `balance +=` in `apply` are not atomic across threads.
  Real, but nothing in the fixture is concurrent, so there is no observable
  failure to demonstrate. Noting rather than reporting.
- `wire/receipt.py:7` `"note": "café"` with `json.dumps` default
  `ensure_ascii=True` escapes to `caf\u00e9`, so the emitted bytes are pure ASCII
  and round-trip cleanly through `.encode("utf-8")` / `.decode("utf-8")`. Correct
  as written.
