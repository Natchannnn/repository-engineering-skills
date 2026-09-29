# Copyright (c) 2026 Example Fixture. MIT License.
"""Receipt serializer. BYTES ARE THE DEDUP IDENTITY (see ledger/dedup.py)."""
import json


def make_receipt(tx_id, amount):
    payload = {"id": tx_id, "amount": amount, "note": "café"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
