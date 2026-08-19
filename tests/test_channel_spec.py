import unittest
from equipment_drivers.channel_spec import parse_channels


class TestParseChannels(unittest.TestCase):
    def test_single_channel(self):
        self.assertEqual(parse_channels("3"), [3])

    def test_comma_list_no_spaces(self):
        self.assertEqual(parse_channels("3,4,5,6"), [3, 4, 5, 6])

    def test_comma_list_with_spaces(self):
        self.assertEqual(parse_channels("3, 4, 5, 6"), [3, 4, 5, 6])

    def test_range(self):
        self.assertEqual(parse_channels("3-6"), [3, 4, 5, 6])

    def test_combination_of_list_and_range(self):
        self.assertEqual(parse_channels("1,3-5,8"), [1, 3, 4, 5, 8])

    def test_duplicates_are_deduped_and_sorted(self):
        self.assertEqual(parse_channels("5,3,4,3-5"), [3, 4, 5])

    def test_all_lowercase(self):
        self.assertEqual(parse_channels("all", channel_count=4), [1, 2, 3, 4])

    def test_all_uppercase(self):
        self.assertEqual(parse_channels("ALL", channel_count=4), [1, 2, 3, 4])

    def test_all_mixed_case(self):
        self.assertEqual(parse_channels("All", channel_count=4), [1, 2, 3, 4])

    def test_all_without_channel_count_raises(self):
        with self.assertRaises(ValueError):
            parse_channels("all")

    def test_invalid_range_start_greater_than_end(self):
        with self.assertRaises(ValueError):
            parse_channels("6-3")

    def test_invalid_non_numeric(self):
        with self.assertRaises(ValueError):
            parse_channels("abc")

    def test_empty_string_raises(self):
        with self.assertRaises(ValueError):
            parse_channels("")

    def test_single_channel_with_channel_count_valid(self):
        self.assertEqual(parse_channels("4", channel_count=8), [4])

    def test_single_channel_out_of_range_raises(self):
        with self.assertRaises(ValueError) as ctx:
            parse_channels("9", channel_count=8)
        self.assertIn("out of range", str(ctx.exception))

    def test_range_out_of_range_raises(self):
        with self.assertRaises(ValueError) as ctx:
            parse_channels("3-10", channel_count=8)
        self.assertIn("out of range", str(ctx.exception))

    def test_comma_list_out_of_range_raises(self):
        with self.assertRaises(ValueError) as ctx:
            parse_channels("1,2,9", channel_count=8)
        self.assertIn("out of range", str(ctx.exception))

    def test_zero_channel_raises(self):
        with self.assertRaises(ValueError) as ctx:
            parse_channels("0")
        self.assertIn(">= 1", str(ctx.exception))

    def test_negative_channel_raises(self):
        with self.assertRaises(ValueError):
            parse_channels("-1")

    def test_zero_in_range_raises(self):
        with self.assertRaises(ValueError) as ctx:
            parse_channels("0-4")
        self.assertIn(">= 1", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
