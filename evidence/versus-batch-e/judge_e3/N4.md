# Findings

## 1. Money values are reconstructed from a JSON float via `Decimal(float)`, corrupting every fractional amount

- **Producer**: `wire/receipt.py:make_receipt` / `wire/receipt.py:_encode` — `json.dumps` serialises `amount` as a bare JSON number, so a Python `float` amount is written in shortest-round-trip decimal form (`0.1`).
- **Consumer**: `ledger/apply.py:apply` — `json.loads` turns that token back into a Python `float`, and line 18 does `balance += Decimal(data["amount"])`. `Decimal(float)` converts the *exact binary expansion* of the double, not its decimal text.
- **Consequence**: Applying a receipt of `make_receipt('t1', 0.1)` sets `balance` to
  `0.1000000000000000055511151231257827021181583404541015625`
  instead of `0.10`. Verified: `apply.apply(wrap(make_receipt('t1', 0.1)))` returns
  `0.1000000000000000055511151231`. Every fractional amount carries ~17 significant digits of binary
  representation error, and repeated accumulation drifts. A ledger of 100 receipts of `0.1` ends at
  `10.00000000000000055511151231257827021181583404541015625` rather than `10.00`.
  `Decimal(str(data["amount"]))` (or having the producer emit `amount` as a JSON string) avoids this.

## 2. Replay identity is the SHA-256 of the raw bytes, not of the receipt, so the same receipt is applied twice

- **Producer**: `wire/receipt.py:make_receipt` → `transport/envelope.py:wrap`. The serialised byte string is
  `{"id": "t1", "amount": 10, "note": "caf\u00e9"}` vs `{"id": "t1", "amount": 10.0, "note": "caf\u00e9"}`
  for the same logical receipt. `json.dumps` preserves the caller's numeric *type*, so `int` and `float`
  spellings of the same amount are different bytes.
- **Consumer**: `ledger/dedup.py:already_applied` — keys `_seen` on `hashlib.sha256(raw).hexdigest()`, i.e. on
  the byte string, and `ledger/apply.py:apply` treats a digest miss as "new receipt".
- **Consequence**: Both calls are emitted by the *same* producer function in the fixture — no external
  re-encoder is required. Verified: `make_receipt('t1', 10)` and `make_receipt('t1', 10.0)` have different
  digests, so after applying the first (`balance == 10.00`) the second returns `balance == 20.00`.
  The same failure occurs for any re-framing relay that changes key order, `ensure_ascii`, or JSON
  whitespace: `json.dumps({'note':'café','amount':'10','id':'t1'}, ensure_ascii=False).encode('utf-8')`
  is a byte-for-byte different encoding of receipt `t1` and drives the balance to `20.00` instead of
  `10`. Deduplication should key on the normalised `(id, amount)` tuple, i.e. on the parsed receipt,
  not on the transport encoding.

## 3. `already_applied` records the digest before the receipt is successfully applied, so a failed receipt is permanently suppressed

- **Producer**: `ledger/dedup.py:already_applied` — line 12 executes `_seen.add(h)` and returns `False`
  *before* the caller has parsed or booked the payload. The function name implies a pure query but it is
  a state-mutating reservation, and there is no commit/abort.
- **Consumer**: `ledger/apply.py:apply` — `dedup.already_applied(raw)` is called at line 15, *before*
  `json.loads` (line 17) and the `Decimal` conversion (line 18) that can raise.
- **Consequence**: For a truncated envelope `b'{"id": "t9", "amount": 1'`, the first `apply.apply` raises
  `json.JSONDecodeError: Expecting ',' delimiter: line 1 column 25 (char 24)` and the balance stays
  `0.00` — but the digest is already in `_seen`. A caller that catches the exception and retries the
  identical bytes (normal at-least-once transport retry) gets a silent no-op: `apply.apply` returns
  `0.00` with no exception. Receipt `t9` is now uncountable forever, because the bytes that would
  represent it are permanently marked "already applied". The reservation should be committed only after
  the balance update succeeds.

## 4. The envelope's `encoding` field is written but never read; the consumer hardcodes UTF-8

- **Producer**: `transport/envelope.py:wrap` — returns `{"payload": raw, "encoding": "utf-8"}`, advertising
  the payload's encoding as part of the contract.
- **Consumer**: `transport/envelope.py:unwrap` returns `env["payload"]` and discards `encoding`;
  `ledger/apply.py:apply` then hardcodes `raw.decode("utf-8")` at line 17.
- **Consequence**: Any producer that sets `"encoding": "latin-1"` for a payload containing the `café`
  note is silently mis-handled. Verified: applying
  `{"payload": b'{"id": "t1", "amount": 1, "note": "caf\xe9"}', "encoding": "latin-1"}` raises
  `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position 38: invalid continuation byte`
  — a hard failure on a byte sequence the producer explicitly declared valid. The declared field is dead
  metadata; either `unwrap` should return it and `apply` should decode accordingly, or `wrap` should not
  advertise it.
