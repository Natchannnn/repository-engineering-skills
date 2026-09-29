# Findings

Reviewed: `wire/receipt.py`, `transport/envelope.py`, `ledger/apply.py`, `ledger/dedup.py`.
Every claim below was reproduced by executing the fixture in place; observed values are quoted verbatim.

---

## 1. Replay guard keys on serialized bytes, not the transaction id the producer emits

- **Producer:** `wire/receipt.py` :: `make_receipt` — writes a stable `"id": tx_id` field into every receipt.
- **Consumer:** `ledger/dedup.py` :: `already_applied` (called from `ledger/apply.py` :: `apply`, line 15).
- **Consequence:** `apply` never reads `data["id"]`; the only thing consulted is `sha256(raw)`. Any change to the payload — including a correction issued under the *same* transaction id — produces a new hash and is applied a second time. Reproduced:
  ```python
  apply.apply(wrap(make_receipt('t1','10.00')))
  apply.apply(wrap(make_receipt('t1','25.00')))
  # -> balance 35.00, _seen has 2 entries
  ```
  A single transaction `t1` contributes `10.00 + 25.00`. The docstring in `dedup.py` ("keyed on the SHA-256 of received BYTES") and the one in `apply.py` ("Applies each unseen receipt exactly once") both describe the guarantee the code does not provide: the guarantee is per-byte-string, not per-transaction.
  The same defect fires in the other direction when two producers serialize the same logical amount differently, which `make_receipt` permits since it never coerces `amount`:
  ```python
  make_receipt('t1', 10.0)   # b'{"amount":10.0,...}'
  make_receipt('t2', 10)     # b'{"amount":10,...}'
  make_receipt('t3','10.00') # b'{"amount":"10.00",...}'
  # three distinct digests, three distinct byte strings, all meaning 10 units
  ```
  Fix: key on `data["id"]` after parsing, and treat the payload digest as a corruption check only.

## 2. `Decimal()` is fed a Python float, importing binary representation error into the balance

- **Producer:** `wire/receipt.py` :: `make_receipt` — `amount` is passed straight into `json.dumps` with no coercion to `str`/`Decimal`.
- **Consumer:** `ledger/apply.py` :: `apply`, line 18 — `Decimal(data["amount"])`.
- **Consequence:** a float `amount` survives the wire as a JSON *number*, and `json.loads` hands `apply` a Python `float`. `Decimal(float)` converts the exact binary value, not the decimal literal the producer intended. Reproduced with a single receipt:
  ```python
  apply.apply(wrap(make_receipt('t1', 0.1)))
  # -> balance 0.1000000000000000055511151231   (expected 0.1)
  ```
  The error is 5.55e-17 on one 0.1-unit receipt and scales linearly with volume; at 1,000,000 such receipts the balance is overstated by ~5.55e-11 — and the intermediate `+=` chain propagates the full 28-digit expansion into every subsequent sum. The module imports `Decimal` specifically to get exact arithmetic and then discards it at the boundary. Fix: have `make_receipt` emit `amount` as a JSON string (`str(Decimal(amount))`) so `apply` only ever sees text.

## 3. Receipts are marked "seen" *before* they are validated, so a malformed receipt is permanently swallowed

- **Producer:** any bytes arriving through `transport/envelope.py` :: `unwrap` (envelope is documented as an opaque carrier that never validates).
- **Consumer:** `ledger/apply.py` :: `apply`, lines 15–18.
- **Consequence:** `dedup.already_applied` inserts the digest into `_seen` as a side effect of the *check*, then `json.loads` / `Decimal` / the `["amount"]` lookup runs and may raise. The failure leaves the digest recorded but nothing applied, converting at-most-once into at-most-zero. Reproduced:
  ```python
  bad = b'{"amount":[1,2]}'
  apply.apply(wrap(bad))  # -> raises ValueError: argument must be a sequence of length 3
  apply.apply(wrap(bad))  # -> returns 0.00, no error
  # _seen has 1 entry, balance 0.00 — this payload can never be applied again
  ```
  The second call takes the `return balance` early-exit at line 16 and reports success. A transient decode error, a truncated frame, or a bad producer becomes a silent, unrecoverable ledger hole. Fix: parse and validate first, then record the digest as the last step (or add an explicit commit/abort).

## 4. `wrap` declares an `encoding` that `unwrap` discards and `apply` ignores

- **Producer:** `transport/envelope.py` :: `wrap`, line 5 — stamps `"encoding": "utf-8"` into the envelope.
- **Consumer:** `transport/envelope.py` :: `unwrap`, line 9 (returns `env["payload"]` only) and `ledger/apply.py` :: `apply`, line 17 (hardcodes `.decode("utf-8")`).
- **Consequence:** the `encoding` field is dead metadata — it is written, never read, and the dict is caller-mutable, so it can be changed after `wrap` returns with no effect. Reproduced by flipping the declared encoding to `latin-1` on a receipt whose note carries `café` as a raw `0xE9` byte:
  ```python
  env['encoding'] = 'latin-1'
  apply.apply(env)   # -> UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 38
  ```
  This compounds finding 3: the `UnicodeDecodeError` happens *after* the digest is recorded, so once the encoding is corrected the receipt is dedup-blocked forever and is silently dropped instead of applied. Fix: have `unwrap` honour `env["encoding"]` and have `apply` decode with it, rejecting unknown values.

## 5. `make_receipt` emits non-JSON tokens for non-finite amounts

- **Producer:** `wire/receipt.py` :: `make_receipt`, line 8 — `json.dumps` with no finite check.
- **Consumer:** any peer on the wire that parses the receipt as RFC 8259 JSON.
- **Consequence:** CPython's encoder emits bare `NaN` / `Infinity`, which are not valid JSON:
  ```python
  make_receipt('t1', float('nan')) -> b'{"amount":NaN,"id":"t1","note":"caf\\u00e9"}'
  make_receipt('t2', float('inf')) -> b'{"amount":Infinity,"id":"t2","note":"caf\\u00e9"}'
  ```
  The in-repo consumer survives only because `json.loads` silently accepts these non-standard extensions by default; a strict parser (Go, Java, Rust, or `json.loads(..., parse_constant=...)` with a guard) rejects the frame. The receipt is therefore valid only to the producer's own dialect, and the divergence is invisible in tests that round-trip through Python. Fix: reject non-finite amounts in `make_receipt`, or pass `allow_nan=False` so the encoder raises instead of emitting garbage.

## 6. An unvalidated `amount` of `NaN` poisons `balance` permanently

- **Producer:** `wire/receipt.py` :: `make_receipt` — forwards `amount` unvalidated, so `'NaN'` and `float('nan')` both reach the wire (see finding 5).
- **Consumer:** `ledger/apply.py` :: `apply`, line 18 — `Decimal(data["amount"])` with no `is_finite()` check.
- **Consequence:** `Decimal('NaN')` is constructed happily and added to the module-level global. Every later `balance += ...` stays `NaN`, and `NaN != NaN` makes the corruption undetectable by comparison:
  ```python
  apply.reset()
  apply.apply(wrap(make_receipt('t3','NaN')))              # -> balance NaN
  apply.apply(wrap(make_receipt('t4','5.00')))            # -> balance NaN  (5.00 lost)
  ```
  The ledger is permanently wrong with no exception raised and no way to detect it from the return value. `reset()` is the only recovery, and it discards all prior legitimate state along with the corruption. Fix: validate `is_finite()` (and the sign / scale policy) before mutating `balance`.

## 7. `_seen` grows without bound, retaining a digest per receipt for the process lifetime

- **Producer:** `ledger/dedup.py` :: `already_applied`, line 12 — unconditional `_seen.add(h)`.
- **Consumer:** `ledger/apply.py` :: `apply` (steady-state ingest) and `ledger/dedup.py` :: `reset` (the only reclaim path, and it wipes the whole ledger's history).
- **Consequence:** dedup state is a pure leak — there is no eviction, no window, and no size cap, and it stores the full 64-char hex digest rather than a truncated one. Measured in this fixture:
  ```python
  # 200,000 receipts through already_applied
  # -> 38.9 MB retained, 195 bytes per receipt
  ```
  At 1M receipts that is ~195 MB resident for a component whose only job is to answer "have I seen this?". Since the guarantee is only per-byte-string (finding 1), the memory buys nothing that a bounded window or a persisted id index would not buy correctly. Fix: store truncated digests and/or a bounded recent-window, and make the retention policy explicit rather than implicit in `reset()`.

---

## Note on completeness of the fixture

There is no caller, entry point, or test in this directory that wires the three modules together: `make_receipt`, `wrap`, and `apply` are each defined but never invoked by anything in the tree, and the only cross-module coupling is the import in `ledger/apply.py`. The producer/consumer contracts above are therefore read from the docstrings and signatures rather than from an observed call graph, and the defects above are ones I confirmed by driving the functions directly. If a runner or test suite was meant to be part of this fixture, it is not present — I did not look outside this directory for it.
