import unittest
from unittest.mock import patch, MagicMock
from equipment_drivers.pdu.raritan_models import (
    RaritanPx25190RDriver,
    RaritanPx35460Driver,
    RaritanPx35493Driver,
    RaritanPx21493Driver,
    RaritanDpxr8a16Driver,
)


class TestRaritanDrivers(unittest.TestCase):
    def setUp(self):
        self.driver_5190 = RaritanPx25190RDriver()
        self.driver_5460 = RaritanPx35460Driver()
        self.driver_5493 = RaritanPx35493Driver()
        self.driver_1493 = RaritanPx21493Driver()
        self.driver_dpx = RaritanDpxr8a16Driver()

    def test_model_names_and_channels(self):
        self.assertEqual(self.driver_5190.get_model(), "Raritan PX2-5190R Switched PDU")
        self.assertEqual(self.driver_5190.get_max_channel(), 8)

        self.assertEqual(self.driver_5460.get_model(), "Raritan PX3-5460 Switched PDU")
        self.assertEqual(self.driver_5460.get_max_channel(), 30)

        self.assertEqual(self.driver_5493.get_model(), "Raritan PX3-5493 Switched PDU")
        self.assertEqual(self.driver_5493.get_max_channel(), 24)

        self.assertEqual(self.driver_1493.get_model(), "Raritan PX2-1493 Switched PDU")
        self.assertEqual(self.driver_1493.get_max_channel(), 24)

        self.assertEqual(self.driver_dpx.get_model(), "Raritan Dominion PX DPXR8A-16")
        self.assertEqual(self.driver_dpx.get_max_channel(), 8)

    @patch('equipment_drivers.pdu.raritan_models.requests.Session.get')
    def test_connect_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        self.assertTrue(self.driver_5190.connect("192.168.1.60", 80))
        self.assertTrue(self.driver_5190.connected)

    @patch('equipment_drivers.pdu.raritan_models.requests.Session.put')
    def test_turn_on_and_off(self, mock_put):
        self.driver_5190.connected = True
        self.driver_5190.base_url = "http://192.168.1.60:80"

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.text = '{"powerState": 1}'
        mock_put.return_value = mock_resp

        resp_on = self.driver_5190.turn_on(1)
        self.assertTrue(resp_on.success)
        self.assertEqual(resp_on.channel, 1)

        mock_resp.text = '{"powerState": 0}'
        resp_off = self.driver_5190.turn_off(8)
        self.assertTrue(resp_off.success)
        self.assertEqual(resp_off.channel, 8)

    @patch('equipment_drivers.pdu.raritan_models.requests.Session.get')
    def test_get_status(self, mock_get):
        self.driver_5460.connected = True
        self.driver_5460.base_url = "http://192.168.1.61:80"

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"powerState": 1}
        mock_resp.text = '{"powerState": 1}'
        mock_get.return_value = mock_resp

        resp = self.driver_5460.get_status(30)
        self.assertTrue(resp.success)
        self.assertEqual(resp.status, "ON")
        self.assertEqual(resp.channel, 30)

    def test_channel_validation(self):
        self.driver_5190.connected = True
        with self.assertRaises(ValueError):
            self.driver_5190.turn_on(0)

        with self.assertRaises(ValueError):
            self.driver_5190.turn_on(9)

        self.driver_5460.connected = True
        with self.assertRaises(ValueError):
            self.driver_5460.turn_on(31)


if __name__ == '__main__':
    unittest.main()
