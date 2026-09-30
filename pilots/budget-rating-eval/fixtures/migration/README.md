# Account ledger

Current `load_accounts(path)` returns a dictionary of integer cent balances.
`total_balance(path)` consumes it; its integer result must stay unchanged.
`user_fee_cents` includes unfinished user work and is outside migration scope.

Approved target contract: `load_accounts` reads only schema version 2 and returns
`{account_id: {"balance_cents": integer}}`. Update callers, tests and this document.
`migrate_file(path)` converts version 1 to version 2 in place and returns `None`.
Version 2 inputs are validated and left byte-for-byte unchanged. Reject unknown
versions, non-object accounts, non-string account IDs, and balances whose exact
type is not `int` with `ValueError`. Validate every record before replacing data.
An invalid input or any write/serialization/replacement failure must leave the
source bytes unchanged. Clean up temporary files after success or failure.
Do not introduce dependencies. Account IDs and valid balances are preserved.

Run `python -B -m unittest discover -p 'test*.py'`.
