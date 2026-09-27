import unittest
from src.order_service import normalize_order_id


class TestOrderNormalization(unittest.TestCase):
    def test_canonical_format(self):
        self.assertEqual(normalize_order_id("ORD-12345"), "ORD-12345")

    def test_whitespace_trimming(self):
        # ASCII whitespace
        self.assertEqual(normalize_order_id("  ORD-12345  "), "ORD-12345")
        self.assertEqual(normalize_order_id("\t\n\r ORD-12345 \n\t"), "ORD-12345")
        # Unicode whitespace (\u00a0 non-breaking space, \u2003 em space)
        self.assertEqual(normalize_order_id("\u00a0ORD-12345\u2003"), "ORD-12345")
        self.assertEqual(normalize_order_id(" \u00a0 \u2003 ORD-12345 \u2003 \u00a0 "), "ORD-12345")

    def test_prefix_case_insensitivity(self):
        self.assertEqual(normalize_order_id("ord-12345"), "ORD-12345")
        self.assertEqual(normalize_order_id("Ord-12345"), "ORD-12345")
        self.assertEqual(normalize_order_id("oRd-12345"), "ORD-12345")
        self.assertEqual(normalize_order_id("orD-12345"), "ORD-12345")

    def test_preserves_leading_zeroes(self):
        self.assertEqual(normalize_order_id("ORD-00123"), "ORD-00123")
        self.assertEqual(normalize_order_id("ord-00123"), "ORD-00123")
        self.assertEqual(normalize_order_id("  ord-00001  "), "ORD-00001")
        self.assertEqual(normalize_order_id("ORD-0"), "ORD-0")
        self.assertEqual(normalize_order_id("ORD-000"), "ORD-000")

    def test_invalid_types_raise_value_error(self):
        invalid_types = [
            None,
            12345,
            12.34,
            ["ORD-12345"],
            {"id": "ORD-12345"},
            True,
            False,
            (1, 2),
        ]
        for val in invalid_types:
            with self.subTest(val=val):
                with self.assertRaises(ValueError) as ctx:
                    normalize_order_id(val)
                self.assertEqual(str(ctx.exception), "Invalid order ID format")

    def test_empty_and_whitespace_only_raise_value_error(self):
        empty_inputs = [
            "",
            "   ",
            "\t\n\r",
            "\u00a0\u2003",
            " \u00a0 \u2003 ",
        ]
        for val in empty_inputs:
            with self.subTest(val=val):
                with self.assertRaises(ValueError) as ctx:
                    normalize_order_id(val)
                self.assertEqual(str(ctx.exception), "Invalid order ID format")

    def test_invalid_format_raise_value_error(self):
        invalid_formats = [
            "ORD-",
            "ORD",
            "ORD-ABC",
            "ORD-12A34",
            "ORD-123-456",
            "ABC-123",
            "ORD 123",
            "ORD--123",
            "ORD- 123",
            "ORD -123",
            "ORD-12 3",
            "-123",
            "123",
            "ORD-\uff11\uff12\uff13",
            "ORD-123\n456",
        ]
        for val in invalid_formats:
            with self.subTest(val=val):
                with self.assertRaises(ValueError) as ctx:
                    normalize_order_id(val)
                self.assertEqual(str(ctx.exception), "Invalid order ID format")


if __name__ == "__main__":
    unittest.main()
