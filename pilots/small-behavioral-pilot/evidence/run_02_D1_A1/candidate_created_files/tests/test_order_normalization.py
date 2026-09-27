import unittest
from src.order_service import normalize_order_id


class TestOrderNormalization(unittest.TestCase):
    def test_standard_format(self):
        self.assertEqual(normalize_order_id("ORD-123"), "ORD-123")
        self.assertEqual(normalize_order_id("ORD-1"), "ORD-1")
        self.assertEqual(normalize_order_id("ORD-987654321"), "ORD-987654321")

    def test_lowercase_and_mixed_case_prefix(self):
        self.assertEqual(normalize_order_id("ord-123"), "ORD-123")
        self.assertEqual(normalize_order_id("Ord-456"), "ORD-456")
        self.assertEqual(normalize_order_id("oRd-789"), "ORD-789")
        self.assertEqual(normalize_order_id("OrD-1011"), "ORD-1011")

    def test_leading_zeroes_preserved(self):
        self.assertEqual(normalize_order_id("ORD-00123"), "ORD-00123")
        self.assertEqual(normalize_order_id("ord-00123"), "ORD-00123")
        self.assertEqual(normalize_order_id("ORD-0"), "ORD-0")
        self.assertEqual(normalize_order_id("ORD-000"), "ORD-000")
        self.assertEqual(normalize_order_id("ord-0000007"), "ORD-0000007")

    def test_ascii_and_unicode_whitespace_stripping(self):
        self.assertEqual(normalize_order_id("  ORD-123  "), "ORD-123")
        self.assertEqual(normalize_order_id("\t\nORD-123\r\n"), "ORD-123")
        self.assertEqual(normalize_order_id("\u00a0ORD-123\u2003"), "ORD-123")
        self.assertEqual(normalize_order_id(" \u00a0 ord-0055 \u2003\u3000 "), "ORD-0055")

    def test_empty_and_whitespace_only_raise_error(self):
        invalid_empty_inputs = ["", "   ", "\t\n", "\u00a0\u2003"]
        for val in invalid_empty_inputs:
            with self.subTest(val=repr(val)):
                with self.assertRaises(ValueError) as ctx:
                    normalize_order_id(val)
                self.assertEqual(str(ctx.exception), "Invalid order ID format")

    def test_non_string_types_raise_error(self):
        invalid_types = [None, 12345, 12.34, True, False, b"ORD-123", ["ORD-123"], {"id": "ORD-123"}]
        for val in invalid_types:
            with self.subTest(val=repr(val)):
                with self.assertRaises(ValueError) as ctx:
                    normalize_order_id(val)
                self.assertEqual(str(ctx.exception), "Invalid order ID format")

    def test_invalid_formats_raise_error(self):
        invalid_formats = [
            "12345",
            "ORD12345",
            "ABC-123",
            "ORDER-123",
            "OR-123",
            "ORD-",
            "ord-",
            "ORD-abc",
            "ORD-123a",
            "ORD-12.3",
            "ORD -123",
            "ORD- 123",
            "ORD--123",
            "ORD-123-456",
            "ORD-+123",
            "ORD-123!",
        ]
        for val in invalid_formats:
            with self.subTest(val=val):
                with self.assertRaises(ValueError) as ctx:
                    normalize_order_id(val)
                self.assertEqual(str(ctx.exception), "Invalid order ID format")


if __name__ == "__main__":
    unittest.main()
