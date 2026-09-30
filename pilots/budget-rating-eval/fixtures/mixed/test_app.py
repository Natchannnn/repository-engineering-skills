import unittest
from app import summarize


class SummaryTest(unittest.TestCase):
    def test_total(self):
        self.assertEqual(summarize([2, 3]), 5)

    def test_empty(self):
        self.assertEqual(summarize([]), 0)
