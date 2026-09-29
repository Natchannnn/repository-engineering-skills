# Feature flags

`add(name, enabled=True, expires_at=None)` registers a flag. `expires_at` is an
optional integer timestamp: the flag is active while `now < expires_at` and expired
at exactly `expires_at`. Unknown names are inactive. `query.active_flags(now)` lists
active flag names in sorted order.

`purge_expired(now)` deletes expired flags and returns how many it removed.
Purging is idempotent: a second call at the same timestamp removes nothing.
