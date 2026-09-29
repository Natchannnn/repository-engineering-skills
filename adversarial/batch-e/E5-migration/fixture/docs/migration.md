# Migration guide (normative for this fixture)

v1 overrides distinguish three states for `interval`:

- key absent → inherit the default (tracks later default changes);
- `null` → disabled;
- `0` → run now.

v2 records carry the state explicitly: `inherit`, `disabled`, `now`, or
`at` + value. The migrator must preserve all three states through a
serialize → restart → re-read round trip. Only the migrator, new tests, and
this guide are in scope. Consumers (`worker/`, v1 reader, merge) stay untouched.
