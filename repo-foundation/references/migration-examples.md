# Migration Examples (atomic vs transitional)

Read in Evolve mode when changing a public contract or persisted schema.

## Atomic replacement (preferred for single-node file state)

```python
tmp = dest.with_suffix(".tmp")
tmp.write_bytes(new_bytes)
os.fsync(tmp.open("rb").fileno())  # durability where supported
os.replace(tmp, dest)  # atomic on same filesystem
```

Invariants: validate inputs + destination ownership before mutation; retain last valid
state until replacement succeeds; test failure boundaries (I/O error, crash mid-write).
Crash during power loss / SIGKILL is out of scope — see README Known Limitations.

## Transitional compatibility (multi-caller migration)

Bad: change producer to `Decimal("5.00")` while callers expect `int 5` → hidden breakage.
Good:
1. Keep old readers working (accept `int | str | Decimal`, normalize internally).
2. Migrate callers one by one (`checkout/cart_summary/invoice` pattern from D2).
3. Add caller AST check + hidden tests enforcing both surfaces during transition.
4. Remove compat shim only after all callers + docs updated.

## Docs sync checklist

- Update `README.md` + CLI help in the same diff as the contract change.
- Do not reference aspirational exports not yet implemented (see BENCHMARK_REPORT overreach note).
