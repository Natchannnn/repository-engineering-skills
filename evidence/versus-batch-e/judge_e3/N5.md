# Findings — E3-run01

Scope reviewed: `wire/receipt.py`, `transport/envelope.py`, `ledger/dedup.py`, `ledger/apply.py`
(plus the three package `__init__.py` stubs, which contain no logic).

Verification method: every finding below was reproduced by executing the fixture
(Python 3.14.5) with `sys.path` pointed at the run directory. No file in the fixture
was modified. Each section cites the observed output that establishes the defect.

---

## Finding 1 — Replay guard is committed *before* the ledger update, so a failed apply silently swallows the receipt forever

**Producer:** `ledger/dedup.py::already_applied` (line 12, `_seen.add(h)`) — the function
inserts the digest into the module-global `_seen` set on every first call, before the
caller has done anything with the payload.

**Consumer:** `ledger/apply.py::apply` (lines 15–19) — calls `dedup.already_applied(raw)`
as a guard, then does `json.loads(...)` (line 17), `data["amount"]` and
`Decimal(...)` (line 18) as separate, fallible steps, and only then rebinds the
global `balance`. The three steps are not atomic with the dedup write, and there is no
rollback of `_seen` on failure.

**Consequence:** The module docstring promises "Applies each unseen receipt exactly
once", but the guard makes it apply *at most* once — including receipts that were never
applied at all. Reproduced with a payload missing `amount`:

```
envelope = wrap(b'{"id":"t1"}')
first  apply -> KeyError: 'amount'   (balance stays Decimal('0.00'))
resend same envelope -> returns Decimal('0.00'), no exception
```

The digest of `b'{"id":"t1"}'` is now in `_seen`, and `apply` line 16 returns the
unchanged balance on every subsequent delivery of those exact bytes. A receipt whose
update failed once is permanently, silently dropped — there is no way for the sender or
the ledger to distinguish "already applied" from "never applied", and no path to
re-drive it. The same leak occurs for a non-UTF-8 payload (`UnicodeDecodeError` at
line 17) and for a non-numeric `amount` (`decimal.InvalidOperation` at line 18).
A retry-on-error caller — the natural response to the first exception — receives a
success-looking `Decimal` and will report the payment as settled.

---

## Finding 2 — `Decimal(<float>)` corrupts the amount when the receipt carries a JSON number

**Producer:** `wire/receipt.py::_fields` (line 11) passes `amount` through to
`_encode` with no type constraint or normalization, and `wire/receipt.py::_encode`
(line 16) hands it to `json.dumps`. If the caller supplies a float, the number is
serialized as a bare JSON number rather than a string.

**Consumer:** `ledger/apply.py::apply` (line 18) calls `Decimal(data["amount"])` on the
decoded value. `Decimal()` applied to a `float` uses the *exact binary* value of that
float, not its decimal literal — the opposite of the `Decimal("...")`-from-string
behaviour the rest of the module is built around (`balance = Decimal("0.00")`, line 9).

**Consequence:** Reproduced end to end:

```
make_receipt("t2", 0.1) -> b'{"id": "t2", "amount": 0.1, "note": "caf\\u00e9"}'
apply(that envelope)    -> balance = Decimal('0.1000000000000000055511151231')
```

A one-cent receipt credits 0.1000000000000000055511151231. Because `_fields` never
pins the type, whether this fires depends entirely on the caller's Python type for the
same logical receipt — the string form `"0.1"` and the float form `0.1` are accepted by
the same producer signature and produce balances that differ from the first significant
digit onward. Repeated accumulation compounds the drift, and the result is not
quantized to the 2 decimal places that `Decimal("0.00")` establishes. `apply` should
reject a non-string `amount` (or decode via `Decimal(str(...))` on a string-validated
path) rather than silently inheriting binary float error into a money balance.

---

## Finding 3 — Dedup key is the full wire blob, not the transaction id, so one transaction can be credited twice

**Producer:** `wire/receipt.py::_encode` (line 15) serializes every field of the receipt
(`id`, `amount`, and the constant `note`) into the byte blob that the transport carries.
The `id` field is the transaction identity, but nothing on the producing side pins a
canonical serialization for `amount` or for `note`.

**Consumer:** `ledger/dedup.py::already_applied` (lines 9–13) keys `_seen` on
`sha256(raw)` of those *bytes*. Two deliveries that differ in any byte outside `id` —
`"10.00"` vs `10.0`, a different `note`, a key-order or whitespace difference from
another producer version — produce different digests and both pass the guard.

**Consequence:** Reproduced by sending the same transaction id twice with the two
serializations the current producer signature already permits:

```
make_receipt("t3", "10.00") -> b'{"id": "t3", "amount": "10.00", "note": "caf\\u00e9"}'
make_receipt("t3", 10.0)    -> b'{"id": "t3", "amount": 10.0,  "note": "caf\\u00e9"}'
sha256 equal: False
apply(both) -> balance = Decimal('20.00')   for a single 10.00 transaction id "t3"
```

The ledger credits 20.00 for a 10.00 receipt. The same root cause is latent on `note`:
`_fields` hardcodes `"café"` today, so it cannot currently be varied from this producer —
but the moment a `note` parameter is added, two deliveries of one transaction that
differ only in the note will both be applied. `wire/receipt.py`'s docstring states the
byte-identity with the historical encoding is deliberate, so the fix belongs at the
boundary: the replay identity should be derived from `id` (or from a canonical
serialization the producer guarantees), not from arbitrary bytes.

---

## Finding 4 — `already_applied` is a non-atomic check-then-act over shared mutable state

**Producer:** `ledger/dedup.py::already_applied` (lines 10–12) performs a membership
test and an insert as two separate operations on the unguarded module-global `_seen`
set, with no lock.

**Consumer:** `ledger/apply.py::apply` (lines 15–18) and `ledger/apply.py::balance`
(line 9) — the balance is likewise a module-global rebound with `+=` (line 18), also
without a lock, and `ledger/apply.py::reset` (lines 22–25) can clear both out from
under an in-flight call.

**Consequence:** For a component whose stated job is "Applies each unseen receipt
exactly once", the uniqueness guarantee does not hold under concurrent delivery. Two
threads entering `apply` with the same envelope can both observe the digest as unseen
(both interleave between line 10's `in` and line 12's `add`) and both reach line 18,
producing `balance = Decimal('20.00')` from one 10.00 receipt. The same unguarded
`+=` means concurrent *distinct* receipts can lose an update outright — `Decimal('5.00')`
and `Decimal('7.00')` applied concurrently can leave `balance = Decimal('5.00')` or
`Decimal('7.00')` rather than `Decimal('12.00')`. If concurrent delivery is not a
supported mode for this ledger, that precondition is not stated anywhere in the module
and nothing enforces it.

---

## Finding 5 — The envelope's `encoding` field is written but never read; the consumer hardcodes UTF-8

**Producer:** `transport/envelope.py::wrap` (line 5) emits `{"payload": raw, "encoding":
"utf-8"}` — the `encoding` key is part of the envelope contract it publishes.

**Consumer:** `transport/envelope.py::unwrap` (line 9) returns `env["payload"]` and
discards `env["encoding"]`; `ledger/apply.py::apply` (line 17) then hardcodes
`raw.decode("utf-8")` instead of honouring the declared encoding.

**Consequence:** The declared field is dead — it is produced but never consumed, so it
can neither be used to detect a mismatch nor to select a codec. An envelope declaring
any other encoding is decoded as UTF-8 anyway and the failure surfaces as an unrelated
decode error rather than a contract violation:

```
env = {"payload": b"caf\xe9", "encoding": "latin-1"}
apply(env) -> UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 3
```

Compounding this, `wrap` hardcodes `"utf-8"` with no parameter, so the field is not
merely unread — it is not writable. The only way to produce a differently-encoded
envelope today is to bypass `wrap` and hand-build the dict, which is precisely the case
above. Every non-UTF-8 producer is therefore silently unsupported, and the failure
lands in `apply` at Finding 1's leak point, where it permanently marks the receipt as
seen. Note also that `wrap` advertises `encoding: "utf-8"` while the bytes it carries
are opaque, so the transport's own docstring guarantee ("Never parses payload") is the
one thing the consumer is violating when it assumes a codec.
