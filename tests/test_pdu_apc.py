import unittest
from unittest.mock import patch, MagicMock
from equipment_drivers.pdu.apc_models import APC_MODELS, ApcAp7900Driver, ApcAp8959Driver


class TestApcDrivers(unittest.TestCase):
    def test_all_apc_models_registered_and_configured(self):
        self.assertEqual(len(APC_MODELS), 20)
        for sig, driver_cls in APC_MODELS.items():
            driver = driver_cls()
            self.assertTrue(driver.get_model().startswith("APC"))
            self.assertGreater(driver.get_max_channel(), 0)
            self.assertEqual(driver.get_channel_count(), driver.get_max_channel())

    def test_sample_channel_counts(self):
        self.assertEqual(APC_MODELS['apc_ap7900']().get_max_channel(), 8)
        self.assertEqual(APC_MODELS['apc_ap7902']().get_max_channel(), 16)
        self.assertEqual(APC_MODELS['apc_ap7930']().get_max_channel(), 24)
        self.assertEqual(APC_MODELS['apc_ap8941']().get_max_channel(), 24)
        self.assertEqual(APC_MODELS['apc_ap8959']().get_max_channel(), 28)
        self.assertEqual(APC_MODELS['apc_ap8958']().get_max_channel(), 20)

    @patch('equipment_drivers.pdu.apc_models.requests.Session.get')
    def test_connect_success(self, mock_get):
        driver = ApcAp7900Driver()
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        self.assertTrue(driver.connect("192.168.1.50", 80, username="user", password="pwd"))
        self.assertTrue(driver.connected)
        self.assertEqual(driver.username, "user")

    @patch('equipment_drivers.pdu.apc_models.requests.Session.put')
    def test_turn_on_and_off(self, mock_put):
        driver = ApcAp7900Driver()
        driver.connected = True
        driver.base_url = "http://192.168.1.50:80"

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.text = "APC_OUTLET_1_ON"
        mock_put.return_value = mock_resp

        resp_on = driver.turn_on(1)
        self.assertTrue(resp_on.success)
        self.assertEqual(resp_on.channel, 1)
        self.assertEqual(resp_on.action, "turn_on")

        mock_resp.text = "APC_OUTLET_1_OFF"
        resp_off = driver.turn_off(1)
        self.assertTrue(resp_off.success)
        self.assertEqual(resp_off.channel, 1)
        self.assertEqual(resp_off.action, "turn_off")

    @patch('equipment_drivers.pdu.apc_models.requests.Session.get')
    def test_get_status(self, mock_get):
        driver = ApcAp7900Driver()
        driver.connected = True
        driver.base_url = "http://192.168.1.50:80"

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"state": "ON"}
        mock_resp.text = '{"state": "ON"}'
        mock_get.return_value = mock_resp

        resp = driver.get_status(3)
        self.assertTrue(resp.success)
        self.assertEqual(resp.status, "ON")
        self.assertEqual(resp.channel, 3)

    def test_channel_validation(self):
        driver = ApcAp7900Driver()
        driver.connected = True
        with self.assertRaises(ValueError):
            driver.turn_on(0)

        with self.assertRaises(ValueError):
            driver.turn_on(9)

        driver_8959 = ApcAp8959Driver()
        driver_8959.connected = True
        with self.assertRaises(ValueError):
            driver_8959.turn_on(29)


if __name__ == '__main__':
    unittest.main()
