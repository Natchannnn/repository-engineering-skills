# V2 fixture: R2 extraction that changes observable error text

`orders.py` (before) — two modules validate quantity with different messages:

```python
# orders.py
def submit_order(qty):
    if not isinstance(qty, int) or qty <= 0:
        raise ValueError("orders: qty must be a positive int")
    ...

# returns.py
def submit_return(qty):
    if not isinstance(qty, int) or qty <= 0:
        raise ValueError("returns: qty must be a positive int, got %r" % (qty,))
    ...
```

Proposed diff (candidate for review): extract `_require_positive_int(qty)` raising
`"qty must be a positive int"` and use it in both places. Tests assert only exception
type, not message — suite stays green. But `returns.py` callers parse the old message
(`got %r` part feeds a support dashboard regex — declared in `docs/support.md`).

Review task: approve or reject the consolidation, with reason.
- Correct verdict: REJECT (or accept only with dashboard update) — observable contract change.
- Our skill says: R2 extraction + "observable text escalates one band" (atk-10 patch, not yet
  in skill text — the run tests the CURRENT text).
- Superpowers says: no risk-band concept; TDD/red-green unaffected (tests green);
  verification-before-completion checks claims, not review judgment.
