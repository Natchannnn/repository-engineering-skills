import unittest
from pathlib import Path
from app import publish_with_retry, receipt_path, receipt_label


class AppTest(unittest.TestCase):
    def test_success(self):
        self.assertEqual(publish_with_retry({"id": "ev-1"}, lambda *a, **k: 7), 7)

    def test_path(self):
        self.assertIsInstance(receipt_path("out"), Path)
        self.assertEqual(receipt_label("out"), "receipt.json")
