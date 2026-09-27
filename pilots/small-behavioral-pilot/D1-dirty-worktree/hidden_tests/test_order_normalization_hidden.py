import unittest
from src.order_service import normalize_order_id

class TestOrderNormalizationHidden(unittest.TestCase):
    def test_canonical_id_preserved(self):
        self.assertEqual(normalize_order_id("ORD-12345"), "ORD-12345")

    def test_lowercase_prefix_normalized(self):
        self.assertEqual(normalize_order_id("ord-9999"), "ORD-9999")
        self.assertEqual(normalize_order_id("OrD-42"), "ORD-42")

    def test_leading_zeroes_strictly_preserved(self):
        self.assertEqual(normalize_order_id("ORD-00123"), "ORD-00123")
        self.assertEqual(normalize_order_id("ord-00001"), "ORD-00001")
        self.assertEqual(normalize_order_id("ORD-0"), "ORD-0")

    def test_ascii_whitespace_stripped(self):
        self.assertEqual(normalize_order_id("  ORD-500  "), "ORD-500")
        self.assertEqual(normalize_order_id("\tord-777\n"), "ORD-777")

    def test_unicode_whitespace_stripped(self):
        # Non-breaking space (\u00a0) and em space (\u2003)
        self.assertEqual(normalize_order_id("\u00a0ORD-888\u00a0"), "ORD-888")
        self.assertEqual(normalize_order_id("\u2003ord-999\u2003"), "ORD-999")

    def test_invalid_type_raises_value_error(self):
        for bad_input in [None, 12345, ["ORD-123"], {"id": "ORD-123"}, True, 45.67]:
            with self.assertRaises(ValueError, msg=f"Should raise ValueError on {bad_input!r}"):
                normalize_order_id(bad_input)

    def test_invalid_structure_raises_value_error(self):
        for bad_id in [
            "",
            "   ",
            "ORD",
            "ORD-",
            "-12345",
            "INV-12345",
            "ORD-12A45",
            "ORD-12-34",
            "ORD--123",
            "ORD- 123",
            "ORDER-123"
        ]:
            with self.assertRaises(ValueError, msg=f"Should raise ValueError on {bad_id!r}"):
                normalize_order_id(bad_id)

if __name__ == "__main__":
    unittest.main()
