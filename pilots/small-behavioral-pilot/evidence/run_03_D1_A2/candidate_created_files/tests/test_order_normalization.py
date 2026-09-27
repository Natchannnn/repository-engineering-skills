import unittest
from src.order_service import normalize_order_id


class TestOrderNormalization(unittest.TestCase):
    def test_standard_order_id(self):
        self.assertEqual(normalize_order_id("ORD-12345"), "ORD-12345")
        self.assertEqual(normalize_order_id("ORD-1"), "ORD-1")
        self.assertEqual(normalize_order_id("ORD-9876543210"), "ORD-9876543210")

    def test_whitespace_trimming_ascii_and_unicode(self):
        # ASCII leading and trailing whitespace
        self.assertEqual(normalize_order_id("   ORD-123   "), "ORD-123")
        self.assertEqual(normalize_order_id("\tORD-123\n"), "ORD-123")
        self.assertEqual(normalize_order_id("\r\n  ORD-123  \t"), "ORD-123")

        # Unicode whitespace (\u00a0 non-breaking space, \u2003 em space, \u3000 ideographic space)
        self.assertEqual(normalize_order_id("\u00a0ORD-123\u00a0"), "ORD-123")
        self.assertEqual(normalize_order_id("\u2003ORD-123\u2003"), "ORD-123")
        self.assertEqual(normalize_order_id(" \u00a0\tORD-123\u2003 \n"), "ORD-123")
        self.assertEqual(normalize_order_id("\u3000ORD-123\u3000"), "ORD-123")

    def test_case_insensitive_prefix(self):
        self.assertEqual(normalize_order_id("ord-123"), "ORD-123")
        self.assertEqual(normalize_order_id("Ord-123"), "ORD-123")
        self.assertEqual(normalize_order_id("oRd-123"), "ORD-123")
        self.assertEqual(normalize_order_id("orD-123"), "ORD-123")
        self.assertEqual(normalize_order_id("ORd-123"), "ORD-123")
        self.assertEqual(normalize_order_id("  ord-456  "), "ORD-456")

    def test_preserves_leading_zeros(self):
        self.assertEqual(normalize_order_id("ORD-00123"), "ORD-00123")
        self.assertEqual(normalize_order_id("ord-00123"), "ORD-00123")
        self.assertEqual(normalize_order_id("Ord-00001"), "ORD-00001")
        self.assertEqual(normalize_order_id("ORD-0"), "ORD-0")
        self.assertEqual(normalize_order_id("ord-000"), "ORD-000")

    def test_invalid_type_raises_value_error(self):
        invalid_types = [None, 12345, 12.34, True, False, ["ORD-123"], {"id": "ORD-123"}, b"ORD-123"]
        for val in invalid_types:
            with self.subTest(val=val):
                with self.assertRaises(ValueError) as ctx:
                    normalize_order_id(val)
                self.assertEqual(str(ctx.exception), "Invalid order ID format")

    def test_empty_and_blank_strings_raise_value_error(self):
        blank_inputs = ["", "   ", "\t\t", "\n\r", "\u00a0", "\u2003", "  \u00a0  \u2003\t "]
        for val in blank_inputs:
            with self.subTest(val=val):
                with self.assertRaises(ValueError) as ctx:
                    normalize_order_id(val)
                self.assertEqual(str(ctx.exception), "Invalid order ID format")

    def test_invalid_format_raises_value_error(self):
        invalid_formats = [
            "ORD-",               # missing number
            "ord-",               # missing number
            "-12345",             # missing prefix
            "12345",              # only digits
            "ORD",                # only prefix
            "ORD12345",           # missing hyphen
            "ORD--123",           # double hyphen
            "ORD-123-456",        # multiple hyphens
            "ORD-12a",            # non-digit character
            "ORD-12.3",           # float notation
            "ORD - 123",          # whitespace inside
            "ORD- 123",           # whitespace after hyphen
            "ORD -123",           # whitespace before hyphen
            "INV-12345",          # wrong prefix
            "ABC-12345",          # wrong prefix
            "ORDER-12345",        # wrong prefix
            "ORD-１２３",          # fullwidth unicode digits
            "ORD-١٢٣",           # arabic-indic digits
        ]
        for val in invalid_formats:
            with self.subTest(val=val):
                with self.assertRaises(ValueError) as ctx:
                    normalize_order_id(val)
                self.assertEqual(str(ctx.exception), "Invalid order ID format")


if __name__ == "__main__":
    unittest.main()
