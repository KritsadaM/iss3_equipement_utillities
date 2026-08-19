import unittest
from unittest.mock import patch, MagicMock
from equipment_drivers.pdu.apc_models import (
    ApcAp7900Driver,
    ApcAp7920Driver,
    ApcAp7921Driver,
    ApcAp8941Driver,
    ApcAp8959Driver,
)


class TestApcDrivers(unittest.TestCase):
    def setUp(self):
        self.driver_7900 = ApcAp7900Driver()
        self.driver_7920 = ApcAp7920Driver()
        self.driver_7921 = ApcAp7921Driver()
        self.driver_8941 = ApcAp8941Driver()
        self.driver_8959 = ApcAp8959Driver()

    def test_model_names_and_channels(self):
        self.assertEqual(self.driver_7900.get_model(), "APC AP7900 Switched Rack PDU")
        self.assertEqual(self.driver_7900.get_max_channel(), 8)

        self.assertEqual(self.driver_7920.get_model(), "APC AP7920 Switched Rack PDU")
        self.assertEqual(self.driver_7920.get_max_channel(), 8)

        self.assertEqual(self.driver_7921.get_model(), "APC AP7921 Switched Rack PDU")
        self.assertEqual(self.driver_7921.get_max_channel(), 8)

        self.assertEqual(self.driver_8941.get_model(), "APC AP8941 Switched Rack PDU 2G")
        self.assertEqual(self.driver_8941.get_max_channel(), 24)

        self.assertEqual(self.driver_8959.get_model(), "APC AP8959 Switched Rack PDU 2G")
        self.assertEqual(self.driver_8959.get_max_channel(), 28)

    @patch('equipment_drivers.pdu.apc_models.requests.Session.get')
    def test_connect_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        self.assertTrue(self.driver_7900.connect("192.168.1.50", 80, username="user", password="pwd"))
        self.assertTrue(self.driver_7900.connected)
        self.assertEqual(self.driver_7900.username, "user")

    @patch('equipment_drivers.pdu.apc_models.requests.Session.put')
    def test_turn_on_and_off(self, mock_put):
        self.driver_7900.connected = True
        self.driver_7900.base_url = "http://192.168.1.50:80"

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.text = "APC_OUTLET_1_ON"
        mock_put.return_value = mock_resp

        resp_on = self.driver_7900.turn_on(1)
        self.assertTrue(resp_on.success)
        self.assertEqual(resp_on.channel, 1)
        self.assertEqual(resp_on.action, "turn_on")

        mock_resp.text = "APC_OUTLET_1_OFF"
        resp_off = self.driver_7900.turn_off(1)
        self.assertTrue(resp_off.success)
        self.assertEqual(resp_off.channel, 1)
        self.assertEqual(resp_off.action, "turn_off")

    @patch('equipment_drivers.pdu.apc_models.requests.Session.get')
    def test_get_status(self, mock_get):
        self.driver_7900.connected = True
        self.driver_7900.base_url = "http://192.168.1.50:80"

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"state": "ON"}
        mock_resp.text = '{"state": "ON"}'
        mock_get.return_value = mock_resp

        resp = self.driver_7900.get_status(3)
        self.assertTrue(resp.success)
        self.assertEqual(resp.status, "ON")
        self.assertEqual(resp.channel, 3)

    def test_channel_validation(self):
        self.driver_7900.connected = True
        with self.assertRaises(ValueError):
            self.driver_7900.turn_on(0)

        with self.assertRaises(ValueError):
            self.driver_7900.turn_on(9)

        self.driver_8959.connected = True
        with self.assertRaises(ValueError):
            self.driver_8959.turn_on(29)


if __name__ == '__main__':
    unittest.main()
