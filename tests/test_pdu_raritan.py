import unittest
from unittest.mock import patch, MagicMock
from equipment_drivers.pdu.raritan_models import RARITAN_MODELS, RaritanPx25190RDriver, RaritanPx35460Driver


class TestRaritanDrivers(unittest.TestCase):
    def test_all_raritan_models_registered_and_configured(self):
        self.assertEqual(len(RARITAN_MODELS), 21)
        for sig, driver_cls in RARITAN_MODELS.items():
            driver = driver_cls()
            self.assertTrue(driver.get_model().startswith("Raritan"))
            self.assertGreater(driver.get_max_channel(), 0)
            self.assertEqual(driver.get_channel_count(), driver.get_max_channel())

    def test_sample_channel_counts(self):
        self.assertEqual(RARITAN_MODELS['raritan_px2_5190r']().get_max_channel(), 8)
        self.assertEqual(RARITAN_MODELS['raritan_px2_5440']().get_max_channel(), 20)
        self.assertEqual(RARITAN_MODELS['raritan_px2_5460']().get_max_channel(), 30)
        self.assertEqual(RARITAN_MODELS['raritan_px2_5804']().get_max_channel(), 42)
        self.assertEqual(RARITAN_MODELS['raritan_px3_5724']().get_max_channel(), 36)
        self.assertEqual(RARITAN_MODELS['raritan_px3_5904']().get_max_channel(), 54)
        self.assertEqual(RARITAN_MODELS['raritan_dpxr12a_16']().get_max_channel(), 12)

    @patch('equipment_drivers.pdu.raritan_models.requests.Session.get')
    def test_connect_success(self, mock_get):
        driver = RaritanPx25190RDriver()
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        self.assertTrue(driver.connect("192.168.1.60", 80))
        self.assertTrue(driver.connected)

    @patch('equipment_drivers.pdu.raritan_models.requests.Session.put')
    def test_turn_on_and_off(self, mock_put):
        driver = RaritanPx25190RDriver()
        driver.connected = True
        driver.base_url = "http://192.168.1.60:80"

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.text = '{"powerState": 1}'
        mock_put.return_value = mock_resp

        resp_on = driver.turn_on(1)
        self.assertTrue(resp_on.success)
        self.assertEqual(resp_on.channel, 1)

        mock_resp.text = '{"powerState": 0}'
        resp_off = driver.turn_off(8)
        self.assertTrue(resp_off.success)
        self.assertEqual(resp_off.channel, 8)

    @patch('equipment_drivers.pdu.raritan_models.requests.Session.get')
    def test_get_status(self, mock_get):
        driver = RaritanPx35460Driver()
        driver.connected = True
        driver.base_url = "http://192.168.1.61:80"

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"powerState": 1}
        mock_resp.text = '{"powerState": 1}'
        mock_get.return_value = mock_resp

        resp = driver.get_status(30)
        self.assertTrue(resp.success)
        self.assertEqual(resp.status, "ON")
        self.assertEqual(resp.channel, 30)

    def test_channel_validation(self):
        driver = RaritanPx25190RDriver()
        driver.connected = True
        with self.assertRaises(ValueError):
            driver.turn_on(0)

        with self.assertRaises(ValueError):
            driver.turn_on(9)

        driver_5460 = RaritanPx35460Driver()
        driver_5460.connected = True
        with self.assertRaises(ValueError):
            driver_5460.turn_on(31)


if __name__ == '__main__':
    unittest.main()
