# Review findings

Scope: `ledger/`, `transport/`, `wire/`. Review-only per SKILL.md "Review vs. Refactor
Authority"; no source file was modified. All consequences below were reproduced by running
the fixture's own modules (Python 3.14.5) in this directory.

---

## 1. Replay guard is committed before the apply succeeds, converting failures into silent no-ops

- **Producer:** `ledger/dedup.py:8` `already_applied(raw)` — inserts the SHA-256 of `raw` into
  the module-global `_seen` on first call and returns `False`, i.e. it registers the receipt
  as *handled* as a side effect of asking whether it was handled.
- **Consumer:** `ledger/apply.py:12` `apply(env)` — calls `dedup.already_applied(raw)` at
  `ledger/apply.py:15`, *then* parses and converts at `ledger/apply.py:17-18`
  (`json.loads`, `Decimal(data["amount"])`). Nothing removes the `_seen` entry if those lines
  raise, and no rollback/try-except exists in either module.
- **Consequence:** the at-most-once window is opened before the value is committed, so a
  receipt that fails mid-apply is permanently poisoned. Reproduced:
  - `apply.apply(wrap(make_receipt('t2', 1.0)[:-1]))` raises
    `json.JSONDecodeError: Expecting ',' delimiter: line 1 column 48 (char 47)`;
    `balance` stays `Decimal('0.00')`.
  - The **immediate redelivery of that identical envelope** returns `Decimal('0.00')` with no
    exception, no log, and no signal that a delivery previously failed. The receipt is
    unrecoverably lost and the second attempt is indistinguishable from a legitimate replay.
  - Same shape for a decode failure: `apply.apply(wrap(bytes([0xff, 0xfe, 0x00])))` raises
    `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0`, and its
    redelivery returns `Decimal('0.00')` silently.
  - Per `references/error-reliability.md` §"Partial Failure"/§"Swallowed Errors" the guard
    is `ledger/dedup.py`'s to own, but the ordering decision belongs to `ledger/apply.py:15`,
    which is the only layer that knows whether the apply succeeded. Risk band: **R3**
    (idempotency/serialization). Not corrected here: changing it alters at-most-once
    semantics, which the module docstring stakes on, so it needs an owner decision.

## 2. Producer emits a JSON number for `amount`; consumer silently inherits binary float error

- **Producer:** `wire/receipt.py:19` `make_receipt(tx_id, amount)` — passes `amount`
  straight through to `json.dumps` in `_encode` (`wire/receipt.py:14`) with no type
  constraint. A numeric argument serializes *unquoted*.
- **Consumer:** `ledger/apply.py:18` `Decimal(data["amount"])` — assumes `amount` is a JSON
  **string** and constructs the `Decimal` from the parsed Python object. A JSON number
  arrives as a `float`, and `Decimal(float)` is exact-binary by definition, not decimal.
- **Consequence:** the money path silently changes value depending on the caller's Python
  type, with no error raised. Reproduced:
  - `make_receipt('t1', '1.10')` (string, intended shape) → `balance == Decimal('1.10')`.
  - `make_receipt('t1', 1.1)` (same receipt, float argument) → `balance ==
    Decimal('1.100000000000000088817841970012523233890533447265625')`, which renders as
    `1.100000000000000088817841970` — 30 significant digits leaking from a ledger seeded at
    `Decimal("0.00")` (`ledger/apply.py:9`).
  - The skew is non-zero and one-directional (always ≥ intended), it compounds across
    receipts, and `dedup` will not help: the two variants also differ in bytes, so they hash
    differently and are both counted — the 1.10 float receipt and its string twin are treated
    as two distinct payments. Note `make_receipt` also rejects the correct
    `Decimal('1.10')` with `TypeError` from `json.dumps`, so the only safe call is an
    untypechecked string, and nothing enforces that. Risk band: **R3** (serialization).
    Correcting means either constraining `make_receipt` to `str` or reading
    `Decimal(str(data["amount"]))` — both are contract-visible, so they are reported, not
    applied.

## 3. `wrap` asserts an encoding it never validated and `unwrap` discards it

- **Producer:** `transport/envelope.py:4` `wrap(raw)` — hardcodes `"encoding": "utf-8"`
  for *any* bytes; the field is a constant, not a fact about `raw`.
- **Consumer:** `ledger/apply.py:17` `raw.decode("utf-8")` — the decode is hardcoded two
  modules away; `transport/envelope.py:8` `unwrap(env)` returns `env["payload"]` and
  ignores `env["encoding"]` entirely.
- **Consequence:** the envelope's one declared contract field is both forged at the producer
  and unread at the consumer, so it provides zero information and actively misleads. Observed:
  `wrap(bytes([0xff, 0xfe, 0x00]))` returns
  `{'payload': b'\xff\xfe\x00', 'encoding': 'utf-8'}` — a well-formed envelope asserting a
  decode that is guaranteed to fail. The failure surfaces two layers away as
  `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte`
  in the ledger, where the ledger cannot distinguish "undecodable payload" from "corrupt
  envelope". Any non-UTF-8 transport variant (a future `charmap` peer, a latin-1 legacy
  source) is rejected with a misleading error and, via finding 1, becomes a permanent silent
  no-op. Risk band: **R2** for the dead field, **R3** for the resulting misdiagnosis. The
  correct owner is `transport/envelope.py`; either validate before labelling or drop the
  field rather than leave a false assertion in a public payload.

## 4. The dedup identity rests on a byte-identity claim that is unverifiable inside this fixture

- **Producer:** `wire/receipt.py:2-3` module docstring — asserts "byte-identical output to
  the historical encoding — the dedup identity is preserved on purpose", resting entirely on
  unfixed `json.dumps` defaults at `wire/receipt.py:16` plus key order from
  `_FIELDS` (`wire/receipt.py:7`).
- **Consumer:** `ledger/dedup.py:2` module docstring and `ledger/dedup.py:9`
  `hashlib.sha256(raw)` — the replay guard is keyed on the exact bytes, so every byte-level
  serialization choice here is load-bearing and permanent.
- **Consequence:** the docstring's invariant is a *hash identity*, and it is enforced by
  nothing. The default `ensure_ascii=True` escapes the non-ASCII `note` value that
  `_fields` (`wire/receipt.py:11`) hardcodes into it. Measured on the same receipt:
  - default → `b'{"id": "t1", "amount": "1.10", "note": "caf\\u00e9"}'` = **51 bytes**
  - `ensure_ascii=False` → `b'{"id": "t1", "amount": "1.10", "note": "caf\xc3\xa9"}'` = **47 bytes**
  - A 4-byte difference yields a completely different SHA-256. If any deployed peer emits
    the other variant, `already_applied` reports `False` for a receipt the local ledger has
    already counted, and `apply` adds it a second time — silent double-counting in a balance
    ledger, with no error and no dedup hit to detect it. The same applies to key ordering.
  - **Fixture gap, stated rather than searched for:** the historical encoder, the golden
    byte fixtures, and any test asserting them are *not present* in this directory (no tests,
    no callers, no VCS metadata). I therefore cannot establish which of the two encodings is
    the real one. Per `references/shared-contracts.md` §3 and the SKILL.md "Hard Stops"
    clause on unexplained historical constraints, the claim is unverifiable as given and the
    byte-identity invariant is unproven. Risk band: **R3–R4** (serialization feeding ledger
    durability). Preserved unchanged; fixing requires the golden bytes, which the fixture
    does not contain.

## 5. Replay-guard set grows without bound and has no eviction path

- **Producer:** `ledger/dedup.py:5` `_seen = set()` — a process-lifetime set; every unique
  receipt appends one 64-character hex digest at `ledger/dedup.py:12` and nothing ever
  removes one.
- **Consumer:** `ledger/apply.py:12` `apply(env)` — the only entry point, and it has no
  lifecycle hook; the sole reclaimer is `ledger/dedup.py:16` `reset()`, reachable only via
  `ledger/apply.py:22` `reset()`, which has **no caller anywhere in this directory**
  (inspection-only conclusion, no test or entrypoint exists here).
- **Consequence:** in any long-lived process rather than a per-batch harness, the guard
  retains ~100 bytes of digest per distinct receipt for the process's entire lifetime, with
  no TTL, size cap, or LRU bound, so memory is monotonically non-decreasing and the
  longest-lived instance is the one that pays. There is also no cap on a hostile or buggy
  producer that varies whitespace, key order, or `1.1` vs `"1.10"` on a repeating payload
  (finding 2), each variation being a fresh entry for the same logical receipt. This is a
  resource-cost finding, not a correctness one: the fixture provides no process-lifetime
  workload to reproduce growth in, so I report the ownership question (does `ledger/dedup.py`
  own a bounded cache, or does the caller own lifetime?) rather than asserting a measured
  failure. Risk band: **R2**.
