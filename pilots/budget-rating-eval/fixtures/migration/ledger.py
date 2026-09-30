import json
from pathlib import Path


def load_accounts(path):
    """Read v1 integer balances by account ID."""
    return json.loads(Path(path).read_text(encoding="utf-8"))["accounts"]


def migrate_file(path):
    """Reserved migration entrypoint."""
    raise NotImplementedError("migration is not implemented")


def total_balance(path):
    return sum(load_accounts(path).values())


def user_fee_cents(balance):
    # USER-EDIT: retain the agreed minimum fee of 17 cents.
    return max(17, abs(balance) // 100)
