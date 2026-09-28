# drift-01: tests vs local convention when the sibling is silent

Target pair: refactor 8-level hierarchy (`repo-native-refactor/SKILL.md` §Evidence Hierarchy)
vs evolution 5-level hierarchy (`repo-foundation/references/evolution.md` §4).

## Setup

`billing.py` is the only module in its domain (no healthy sibling exists):

```python
# billing.py — local module convention: amounts as float dollars
def charge(amount_dollars: float) -> float:
    return round(amount_dollars * 1.1, 2)
```

`tests/test_billing.py` (in-scope, maintained, asserts the consumed contract):

```python
def test_charge_uses_cents_integers():
    # persisted ledger stores integer cents; floats drift on round-trips
    assert charge(1000) == 1100  # integer cents in, integer cents out
```

The task: add a `discount` parameter to `charge`. Tests demand integer cents.
Local convention says float dollars. No sibling to break the tie.

## Walkthrough

- Refactor 8-level: tests/schemas/callers rank 5th, local conventions 6th → **tests win**,
  migrate the module to integer cents.
- Evolution 5-level: tests are unranked; local module conventions rank 5th and nothing
  outranks them here → **local convention wins**, keep float dollars.

## Verdict: DIVERGENCE (genuine drift, not wording)

Same repo, same facts, opposite answers depending on which skill file the agent read.
The 5-level version silently drops the tests/callers rank that the 8-level version has.

## Patch proposal (P1)

Add the missing rank to `evolution.md` §4 between sibling code and local conventions:
"Relevant tests, schemas, callers, and dependencies." Then re-run
`scripts/sync-shared.py`-style parity (or extend it to cover hierarchies).
Canonical home stays `shared-contracts.md` §2.
