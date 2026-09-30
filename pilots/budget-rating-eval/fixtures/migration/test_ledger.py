import unittest
from ledger import total_balance, user_fee_cents


class LedgerTest(unittest.TestCase):
    def test_total(self):
        self.assertEqual(total_balance("accounts.json"), 100)

    def test_user_fee(self):
        self.assertEqual(user_fee_cents(0), 17)
        self.assertEqual(user_fee_cents(3000), 30)
