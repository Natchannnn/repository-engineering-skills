# V3 fixture: planted bug on superpowers home turf

`tiers.py`:

```python
TIERS = [(100, 0.0), (500, 0.05), (1000, 0.10)]

def discount_rate(amount):
    rate = 0.0
    for threshold, r in TIERS:
        if amount > threshold:
            rate = r
    return rate

def total(amount):
    return amount * (1 - discount_rate(amount))
```

Bug: `>` should be `>=` (buy exactly 500 → misses 5%). Red herring: `total()` float
rounding looks suspicious but is fine. Hidden check: `total(500) == 475.0`.

Task: fix so the hidden check passes without breaking `total(100) == 100.0`.
- Superpowers path: reproduce first, single hypothesis, red-green regression test.
- Our skills path: no reproduce-first rule; verification rigor + final-state check only.
- A0: bare prompt, fix directly.
