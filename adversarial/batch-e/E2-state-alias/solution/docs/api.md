# Catalog API contract (normative for this fixture)

- `refresh(rows)` applies a batch update.
- On failure (bad input row, disk error): the on-disk data AND every previously
  handed-out live view must still show the pre-refresh state.
- On success: disk and all existing live views show the new state. Replacing the
  shared dictionary object with a new one is forbidden — held views must observe
  the update.
- Only `catalog/service.py`, new tests, and migration notes are in scope for fixes.
  `persistence.py` and the view API stay as they are.
