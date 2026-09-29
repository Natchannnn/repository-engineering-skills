# Copyright (c) 2026 Example Fixture. MIT License.
"""Balance ledger. Applies each unseen receipt exactly once."""
import json
from decimal import Decimal

from transport.envelope import unwrap
from ledger import dedup

balance = Decimal("0.00")


def apply(env):
    global balance
    raw = unwrap(env)
    if dedup.already_applied(raw):
        return balance
    data = json.loads(raw.decode("utf-8"))
    balance += Decimal(data["amount"])
    return balance


def reset():
    global balance
    balance = Decimal("0.00")
    dedup.reset()
