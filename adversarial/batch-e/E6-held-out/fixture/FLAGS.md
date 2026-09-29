# Feature flags

`add(name, enabled=True)` registers a flag. `is_active(name, now)` reports whether
it is currently active. Unknown names are inactive. `query.active_flags(now)` lists
active flag names in sorted order.
