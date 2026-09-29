# Findings — ledger / transport / wire fixture

Review-only pass. No source file was modified. All consequences below were
reproduced by running the fixture as-is (verification section at the end).

---

## 1. Replay guard commits before the balance is mutated, so any failure mid-apply permanently discards the receipt

- **Risk band:** R3 (semantic — idempotency / money), escalating to R4 for the
  balance value itself.
- **Producer:** `ledger/dedup.py:8` `already_applied(raw: bytes)` — inserts the
  SHA-256 hex into the module-global `_seen` set at `ledger/dedup.py:12` and
  returns `False`, *before* the caller has done any work. The function name reads
  as a pure query; the insert makes it a write-committing predicate.
- **Consumer:** `ledger/apply.py:12` `apply(env)` — calls
  `dedup.already_applied(raw)` at `ledger/apply.py:15`, then performs
  `json.loads(raw.decode("utf-8"))` (`ledger/apply.py:17`) and
  `balance += Decimal(data["amount"])` (`ledger/apply.py:18`). Anything that
  raises in between leaves `_seen` and `balance` permanently divergent, and
  there is no rollback of the recorded hash.
- **Consequence:** a single exception between the guard and the addition turns
  one receipt into a permanently lost, permanently silent credit. Observed:
  `apply(wrap(b'{"amount": "oops"}'))` raises `decimal.InvalidOperation` on the
  first call; the identical second call returns `Decimal('0.00')` with **no
  exception**, because the hash is already in `_seen` and `apply` short-circuits
  at `ledger/apply.py:16`. Final state: `balance == Decimal('0.00')`, the receipt
  is recorded as applied, and the caller receives a success-looking return value.
  Retrying the delivery never recovers it; only `reset()` clears it. Because the
  ledger is the money boundary, a transient parse/decimal failure becomes a
  silent zero-amount receipt rather than a retryable error.
- **Correction direction (not applied — review only):** the guard should not
  commit the seen-mark until the addition has succeeded, or the two pieces of
  state must be advanced together (record-then-apply with rollback on failure, or
  separate `is_seen` / `mark_seen` so the consumer owns the commit point).
  Renaming `already_applied` to reflect that it mutates is an R2 follow-on, not
  the primary fix. Per `references/error-reliability.md` and the R4 policy in
  `references/semantic-risk.md`, this needs an explicit owner decision on
  idempotency before any change — the current "record first" order is a
  deliberate-looking choice and must not be silently reversed.

---

## 2. The envelope's declared `encoding` field is produced but never consumed; `apply` hardcodes UTF-8

- **Risk band:** R2 (contextual structural) for the dead field, R3 for the
  decode path because it feeds the failure in finding 1.
- **Producer:** `transport/envelope.py:4` `wrap(raw: bytes)` — emits
  `{"payload": raw, "encoding": "utf-8"}`, so `encoding` is a declared part of
  the wire contract written on every envelope.
- **Consumer:** `transport/envelope.py:8` `unwrap(env)` returns only
  `env["payload"]`, discarding `encoding`; `ledger/apply.py:17` then hardcodes
  `.decode("utf-8")` in the payload's place. Nothing in the fixture ever reads
  the `encoding` key.
- **Consequence:** the field is a contract with zero consumers, and the actual
  decode policy is a second, undeclared source of truth in a different package.
  Any envelope that honestly declares its encoding is decoded under the wrong
  one. Observed with
  `{"payload": b'{"amount":"5.00","note":"caf\xc3\xa9"}' … encoded latin-1 …,
  "encoding": "latin-1"}`: `apply` raises
  `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 28`
  and `balance` stays `Decimal('0.00')` — even though the envelope declared the
  encoding that would have decoded it. This is the same `note` value
  `wire/receipt.py:7` emits as `"café"`, so the fixture contains a non-ASCII
  receipt that makes the mismatch reachable. Compounding: this failure poisons
  the dedup set, so the same envelope replayed later returns `Decimal('0.00')`
  silently (see finding 1).
- **Correction direction (not applied — review only):** either `unwrap` should
  return the payload decoded per the envelope's declared `encoding` (making the
  field load-bearing and removing the hardcoded literal from `ledger`), or
  `wrap` should stop emitting a field nothing honors. Do not delete
  `encoding` unilaterally — it is serialized output and may be consumed by code
  outside this fixture; that surface is not visible here.

---

## 3. The dedup key covers the whole receipt, so non-identity fields (`note`, JSON escaping style) can double-credit one transaction

- **Risk band:** R3 (semantic — idempotency), R4 for the resulting balance.
- **Producer:** `wire/receipt.py:6` `make_receipt(tx_id, amount)` — builds
  `{"id": tx_id, "amount": amount, "note": "café"}`. `id` is the transaction
  identity; `note` is free text that carries no ledger meaning.
- **Consumer:** `ledger/dedup.py:8` `already_applied(raw: bytes)` — hashes the
  entire receipt, `hashlib.sha256(raw)` at `ledger/dedup.py:9`, so every byte
  of the payload including `note` participates in the replay identity. The
  docstrings at `wire/receipt.py:2` and `ledger/dedup.py:2` document
  bytes-as-identity, and `ledger/apply.py:2` promises "each unseen receipt
  exactly once", so the defect is specifically that the *identity* is wider than
  the transaction, not that byte-keying was chosen.
- **Consequence — two demonstrated double-credits of a single transaction:**
  - Free-text drift. `make_receipt("t9", "10.00")` then a re-send of the same
    transaction as `{"id":"t9","amount":"10.00","note":"cafe"}` (same `id`, same
    `amount`, unaccented note) → two distinct SHA-256 values → `balance` goes
    `10.00` → `20.00`. A single transaction is credited twice, and the
    divergence is invisible because both applications are individually correct.
  - Serializer drift, no semantic change at all.
    `json.dumps(...)` in `wire/receipt.py:8` uses the default
    `ensure_ascii=True`, so `"café"` is emitted as the six bytes `caf\u00e9`.
    The byte-identical receipt expressed with `ensure_ascii=False` (the literal
    UTF-8 `caf\xc3\xa9`) → distinct hash → `balance` goes `7.00` → `14.00`. Two
    encodings of the *same* receipt double-apply, and `make_receipt` is not the
    only possible producer of an envelope for a given transaction.
- **Correction direction (not applied — review only):** key the guard on a
  canonical field (e.g. `id`) rather than the full payload, or canonicalize
  before hashing. This is an intentional, documented contract decision, so per
  the R4 stop condition in `references/semantic-risk.md` the recommendation is
  *report and decide*, not mutate: if byte-identity is genuinely required for
  transport-level replay detection, then the wire serializer must be the single
  enforced canonical form (`ensure_ascii` fixed, `sort_keys` and `separators`
  already fixed there) and that invariant needs to be stated as a producer
  obligation. Either way the current state is unsafe for a money balance.

---

## Notes

- No tests, no packaging metadata, and no other callers of these modules exist in
  this fixture, so the "healthy sibling precedent" rung of the evidence
  hierarchy could not be consulted. Each finding above rests on the fixture's
  own docstrings plus reproduced runtime behavior.
- `ledger/apply.py:9` module-global `balance` and the `reset()` helper at
  `ledger/apply.py:22` are the only other mutable state; they are consistent with
  each other, so I did not raise a separate finding. Note that `reset()` clears
  `_seen` too, which is why findings 1 and 2 are recoverable only in tests.
- Items 1 and 2 are causally linked: the decode failure in finding 2 is
  converted into a silent drop by finding 1. Fixing the commit order (finding 1)
  is the higher-value of the two; finding 2 is still independently a dead
  contract.

## Verification performed

Read-only inspection of `ledger/{__init__,dedup,apply}.py`,
`transport/{__init__,envelope}.py`, `wire/{__init__,receipt}.py`, plus the skill
and its four routed references. All runtime claims above were reproduced by
piping ad-hoc Python into the interpreter from this directory (no files created
or modified other than this report):

- finding 1: `apply(wrap(b'{"amount": "oops"}'))` → `InvalidOperation`, then
  re-apply → `Decimal('0.00')`, `balance == Decimal('0.00')`.
- finding 2: latin-1 `encoding` envelope with `café` → `UnicodeDecodeError` at
  `ledger/apply.py:17`, `balance == Decimal('0.00')`, and the payload confirmed
  already recorded in `dedup._seen`.
- finding 3: same `id` with a changed `note` → `20.00`; `ensure_ascii=True` vs
  `False` forms of one receipt → `14.00`.

No repository-native lint, type-check, or test command exists in this fixture,
so none was run and none is claimed.
