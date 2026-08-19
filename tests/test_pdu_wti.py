import unittest
from unittest.mock import patch, MagicMock
import requests
from equipment_drivers.pdu.wti_models import (
    BaseWtiPduDriver,
    WtiVmrHd4d20Driver,
    WtiVmr16Hd20Driver,
    WtiNps8Hd20Driver,
    WtiIps800Driver,
    WtiCpm800Driver,
)


class TestWtiDrivers(unittest.TestCase):
    def setUp(self):
        self.driver_hd20 = WtiVmrHd4d20Driver()
        self.driver_16hd = WtiVmr16Hd20Driver()
        self.driver_nps = WtiNps8Hd20Driver()
        self.driver_ips = WtiIps800Driver()
        self.driver_cpm = WtiCpm800Driver()
        self.ip = "192.168.1.40"
        self.port = 80

    def test_model_names_and_channels(self):
        self.assertEqual(self.driver_hd20.get_model(), "WTI VMR-HD4D20 C19")
        self.assertEqual(self.driver_hd20.get_max_channel(), 20)

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

        result = self.driver_hd20.connect(self.ip, self.port)
        self.assertTrue(result)
        self.assertTrue(self.driver_hd20.connected)
        mock_get.assert_called_once()

    @patch('equipment_drivers.pdu.wti_models.requests.Session.get')
    def test_connect_with_credential_override(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.driver_hd20.connect(self.ip, self.port, username="custom_user", password="custom_pass")
        self.assertTrue(result)
        self.assertEqual(self.driver_hd20.username, "custom_user")
        self.assertEqual(self.driver_hd20.password, "custom_pass")
        self.assertEqual(self.driver_hd20.auth.username, "custom_user")
        self.assertEqual(self.driver_hd20.auth.password, "custom_pass")

    @patch('equipment_drivers.pdu.wti_models.requests.Session.get')
    def test_connect_without_override_keeps_default_credentials(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        self.driver_hd20.connect(self.ip, self.port)
        self.assertEqual(self.driver_hd20.username, "admin")
        self.assertEqual(self.driver_hd20.password, "admin")

    @patch('equipment_drivers.pdu.wti_models.requests.Session.put')
    @patch('equipment_drivers.pdu.wti_models.BaseWtiPduDriver.get_channel_count', return_value=20)
    def test_turn_on(self, mock_count, mock_put):
        self.driver_hd20.connected = True
        self.driver_hd20.base_url = f"http://{self.ip}:{self.port}/api/v2"

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = "OK_RAW"
        mock_put.return_value = mock_response

        response = self.driver_hd20.turn_on(1)
        self.assertTrue(response.success)
        self.assertEqual(response.raw, "OK_RAW")
        self.assertEqual(response.action, "turn_on")
        self.assertEqual(response.channel, 1)
        mock_put.assert_called_once_with(
            f"http://{self.ip}:{self.port}/api/v2/plugs/1",
            json={"action": 1},
            auth=self.driver_hd20.auth,
            timeout=self.driver_hd20.timeout
        )

    @patch('equipment_drivers.pdu.wti_models.requests.Session.get')
    @patch('equipment_drivers.pdu.wti_models.BaseWtiPduDriver.get_channel_count', return_value=20)
    def test_get_status_on(self, mock_count, mock_get):
        self.driver_hd20.connected = True
        self.driver_hd20.base_url = f"http://{self.ip}:{self.port}/api/v2"

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"status": 1}
        mock_response.text = '{"status": 1}'
        mock_get.return_value = mock_response

        response = self.driver_hd20.get_status(2)
        self.assertEqual(response.status, "ON")
        self.assertEqual(response.raw, '{"status": 1}')
        self.assertTrue(response.success)
        self.assertEqual(response.channel, 2)

    @patch('equipment_drivers.pdu.wti_models.requests.Session.get')
    def test_get_channel_count_from_device(self, mock_get):
        self.driver_hd20.connected = True
        self.driver_hd20.base_url = f"http://{self.ip}:{self.port}/api/v2"

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = [{"id": i} for i in range(1, 9)]
        mock_get.return_value = mock_response

        self.assertEqual(self.driver_hd20.get_channel_count(), 8)

    @patch('equipment_drivers.pdu.wti_models.requests.Session.get')
    def test_get_channel_count_falls_back_on_error(self, mock_get):
        self.driver_hd20.connected = True
        self.driver_hd20.base_url = f"http://{self.ip}:{self.port}/api/v2"
        mock_get.side_effect = requests.exceptions.ConnectionError("unreachable")

        self.assertEqual(self.driver_hd20.get_channel_count(), WtiVmrHd4d20Driver.DEFAULT_CHANNEL_COUNT)

    @patch('equipment_drivers.pdu.wti_models.BaseWtiPduDriver.get_channel_count', return_value=20)
    def test_out_of_range_channel_raises_value_error(self, mock_count):
        self.driver_hd20.connected = True
        self.driver_hd20.base_url = f"http://{self.ip}:{self.port}/api/v2"

        with self.assertRaises(ValueError) as ctx:
            self.driver_hd20.turn_on(0)
        self.assertIn("out of range", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.driver_hd20.turn_off(21)
        self.assertIn("out of range", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.driver_hd20.get_status(-1)
        self.assertIn("out of range", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
