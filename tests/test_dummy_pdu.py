import unittest
from equipment_drivers.pdu.dummy_pdu import DummyPDUDriver


class TestDummyPDUDriver(unittest.TestCase):
    def setUp(self):
        self.driver = DummyPDUDriver()
        self.driver.connect("192.168.1.10", 161)

    def test_channel_count(self):
        self.assertEqual(self.driver.get_channel_count(), 8)
        self.assertEqual(self.driver.get_max_channel(), 8)

    def test_valid_channels(self):
        resp_on = self.driver.turn_on(1)
        self.assertTrue(resp_on.success)
        self.assertEqual(resp_on.channel, 1)

        resp_off = self.driver.turn_off(8)
        self.assertTrue(resp_off.success)
        self.assertEqual(resp_off.channel, 8)

        resp_status = self.driver.get_status(4)
        self.assertTrue(resp_status.success)
        self.assertEqual(resp_status.status, "ON")

    def test_out_of_range_channels(self):
        with self.assertRaises(ValueError) as ctx:
            self.driver.turn_on(0)
        self.assertIn("out of range", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.driver.turn_off(9)
        self.assertIn("out of range", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.driver.get_status(99)
        self.assertIn("out of range", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.driver.validate_channel(-5)
        self.assertIn("out of range", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
