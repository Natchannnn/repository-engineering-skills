# Copyright (c) 2026 Example Fixture. MIT License.
"""Evaluator for E3. BRANCH_DIR selects variant; separate process each run."""
import json
import os
import pathlib
import sys
import unittest
from decimal import Decimal

BRANCH = pathlib.Path(
    os.environ.get("BRANCH_DIR", pathlib.Path(__file__).parent.parent / "branch-defect")
).resolve()
sys.path.insert(0, str(BRANCH))

from transport import envelope  # noqa: E402
from ledger import apply as ledger  # noqa: E402
from wire import receipt  # noqa: E402

HISTORICAL = json.dumps({"id": "tx1", "amount": "12.50", "note": "café"}).encode("utf-8")


class RetryTest(unittest.TestCase):
    def setUp(self):
        ledger.reset()

    def test_historical_retry_is_idempotent(self):
        ledger.apply(envelope.wrap(HISTORICAL))  # the already-applied receipt
        self.assertEqual(ledger.balance, Decimal("12.50"))
        ledger.apply(envelope.wrap(receipt.make_receipt("tx1", "12.50")))  # retry
        self.assertEqual(
            ledger.balance,
            Decimal("12.50"),
            f"expected balance Decimal('12.50'), got Decimal('{ledger.balance}')",
        )


if __name__ == "__main__":
    unittest.main()
