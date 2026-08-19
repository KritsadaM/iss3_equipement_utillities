import unittest
from unittest.mock import patch, MagicMock
from equipment_drivers.pdu.wti_models import (
    WtiVmr16Hd20Driver,
    WtiNps8Hd20Driver,
    WtiIps800Driver,
    WtiCpm800Driver,
)


class TestWtiModels(unittest.TestCase):
    def setUp(self):
        self.driver_16hd = WtiVmr16Hd20Driver()
        self.driver_nps = WtiNps8Hd20Driver()
        self.driver_ips = WtiIps800Driver()
        self.driver_cpm = WtiCpm800Driver()

    def test_model_names_and_channels(self):
        self.assertEqual(self.driver_16hd.get_model(), "WTI VMR-16HD20 Switched PDU")
        self.assertEqual(self.driver_16hd.get_max_channel(), 16)

        self.assertEqual(self.driver_nps.get_model(), "WTI NPS-8HD20 Network Power Switch")
        self.assertEqual(self.driver_nps.get_max_channel(), 8)

        self.assertEqual(self.driver_ips.get_model(), "WTI IPS-800 Internet Power Switch")
        self.assertEqual(self.driver_ips.get_max_channel(), 8)

        self.assertEqual(self.driver_cpm.get_model(), "WTI CPM-800 Control Port Manager")
        self.assertEqual(self.driver_cpm.get_max_channel(), 8)

    @patch('equipment_drivers.pdu.wti_models.requests.Session.get')
    def test_connect_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        self.assertTrue(self.driver_16hd.connect("192.168.1.41", 80))
        self.assertTrue(self.driver_16hd.connected)

    @patch('equipment_drivers.pdu.wti_models.requests.Session.put')
    @patch('equipment_drivers.pdu.wti_models.BaseWtiPduDriver.get_channel_count', return_value=16)
    def test_turn_on_and_off(self, mock_count, mock_put):
        self.driver_16hd.connected = True
        self.driver_16hd.base_url = "http://192.168.1.41:80/api/v2"

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.text = '{"status": 1}'
        mock_put.return_value = mock_resp

        resp_on = self.driver_16hd.turn_on(16)
        self.assertTrue(resp_on.success)
        self.assertEqual(resp_on.channel, 16)

        mock_resp.text = '{"status": 0}'
        resp_off = self.driver_16hd.turn_off(16)
        self.assertTrue(resp_off.success)
        self.assertEqual(resp_off.channel, 16)

    def test_channel_validation(self):
        self.driver_16hd.connected = False
        with self.assertRaises(ValueError):
            self.driver_16hd.validate_channel(0)

        with self.assertRaises(ValueError):
            self.driver_16hd.validate_channel(17)

        self.driver_nps.connected = False
        with self.assertRaises(ValueError):
            self.driver_nps.validate_channel(9)


if __name__ == '__main__':
    unittest.main()
