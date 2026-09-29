# Copyright (c) 2026 Example Fixture. MIT License.
"""Receipt serializer (clean variant). Restructured internals, byte-identical output
to the historical encoding — the dedup identity is preserved on purpose."""

import json

_FIELDS = ("id", "amount", "note")


def _fields(tx_id, amount):
    return {"id": tx_id, "amount": amount, "note": "café"}


def _encode(payload):
    ordered = {k: payload[k] for k in _FIELDS}
    return json.dumps(ordered).encode("utf-8")


def make_receipt(tx_id, amount):
    return _encode(_fields(tx_id, amount))
